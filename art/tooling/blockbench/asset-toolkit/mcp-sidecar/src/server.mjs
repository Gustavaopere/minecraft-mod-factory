import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { startBridgeGateway } from './bridge_gateway.mjs';

const require = createRequire(import.meta.url);
const { TOOL_NAMES, TOOL_DESCRIPTIONS } = require('../tool_manifest.cjs');
const { createSession } = require('../../live-bridge/session_manager.js');
const { bridgeError } = require('../../live-bridge/protocol.js');

const emptySchema = z.object({}).strict();
const animationSchema = z.object({
  animationId: z.string().min(1).max(256).optional(),
  name: z.string().min(1).max(256).optional(),
}).strict().refine((value) => Boolean(value.animationId || value.name), 'animationId or name is required');
const pluginSchema = z.object({pluginId: z.string().min(1).max(128)}).strict();
const profileIdSchema = z.object({profileId: z.string().min(1).max(128)}).strict();
const contractSchema = z.object({
  profile: z.object({
    requiredBones: z.array(z.string().min(1).max(128)).max(256).optional(),
    requiredAnimations: z.array(z.string().min(1).max(256)).max(256).optional(),
    maxSpan: z.tuple([z.number().finite().nonnegative(), z.number().finite().nonnegative(), z.number().finite().nonnegative()]).optional(),
  }).strict(),
}).strict();

function schemaFor(name) {
  if (name === 'blockbench.get_animation') return animationSchema;
  if (name === 'blockbench.validate_contract') return contractSchema;
  if (name === 'blockbench.extensions.get' || name === 'blockbench.extensions.check_compatibility') return pluginSchema;
  if (name === 'blockbench.profiles.get' || name === 'blockbench.profiles.resolve_for_asset') return profileIdSchema;
  return emptySchema;
}

function boundedString(value, field, fallback = 'UNRESOLVED', maxLength = 256) {
  const candidate = value === undefined || value === null || value === '' ? fallback : value;
  if (typeof candidate !== 'string' || !candidate.trim() || candidate.length > maxLength) {
    throw bridgeError('INVALID_RUNTIME_CONTEXT', field);
  }
  return candidate.trim();
}

function normalizeRuntimeContext(input = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw bridgeError('INVALID_RUNTIME_CONTEXT');
  const physicalProviders = Array.isArray(input.physicalProviders) ? input.physicalProviders : [];
  const authorizedExtensions = Array.isArray(input.mcpAuthorizedExtensionIds) ? input.mcpAuthorizedExtensionIds : [];
  if (physicalProviders.length > 256 || authorizedExtensions.length > 256) throw bridgeError('INVALID_RUNTIME_CONTEXT', 'entry limit');

  return Object.freeze({
    minecraftVersion: boundedString(input.minecraftVersion, 'minecraftVersion'),
    loader: boundedString(input.loader, 'loader'),
    javaVersion: boundedString(input.javaVersion, 'javaVersion'),
    activeProviderProfile: boundedString(input.activeProviderProfile, 'activeProviderProfile'),
    physicalProviders: physicalProviders.map((entry) => {
      if (!entry || typeof entry !== 'object' || Array.isArray(entry)) throw bridgeError('INVALID_RUNTIME_CONTEXT', 'physicalProviders');
      return {
        modId: boundedString(entry.modId, 'physicalProviders.modId', null, 128),
        version: boundedString(entry.version, 'physicalProviders.version', null),
        presence: boundedString(entry.presence, 'physicalProviders.presence', 'PRESENT', 64),
        health: boundedString(entry.health, 'physicalProviders.health', 'UNPROVEN', 64),
      };
    }),
    mcpAuthorizedExtensionIds: authorizedExtensions.map((id) => boundedString(id, 'mcpAuthorizedExtensionIds', null, 128)),
  });
}

function parseJsonArray(raw, field) {
  if (raw === undefined || raw === null || raw === '') return [];
  let value;
  try { value = JSON.parse(raw); }
  catch (_) { throw bridgeError('INVALID_RUNTIME_CONTEXT', `${field} JSON`); }
  if (!Array.isArray(value)) throw bridgeError('INVALID_RUNTIME_CONTEXT', field);
  return value;
}

export function contextFromEnvironment(env = process.env) {
  return normalizeRuntimeContext({
    minecraftVersion: env.RPG_ASSET_MINECRAFT_VERSION,
    loader: env.RPG_ASSET_LOADER,
    javaVersion: env.RPG_ASSET_JAVA_VERSION,
    activeProviderProfile: env.RPG_ASSET_PROVIDER_PROFILE,
    physicalProviders: parseJsonArray(env.RPG_ASSET_PHYSICAL_PROVIDERS_JSON, 'physicalProviders'),
    mcpAuthorizedExtensionIds: parseJsonArray(env.RPG_ASSET_MCP_EXTENSIONS_JSON, 'mcpAuthorizedExtensionIds'),
  });
}

export function createServer(options = {}) {
  const callBridge = typeof options.callBridge === 'function'
    ? options.callBridge
    : async () => { throw new Error('BRIDGE_UNAVAILABLE'); };
  const server = new McpServer({name: 'rpg-asset-mcp', version: '0.1.0'});
  for (const name of TOOL_NAMES) {
    server.registerTool(
      name,
      {
        description: TOOL_DESCRIPTIONS[name],
        inputSchema: schemaFor(name),
        annotations: {readOnlyHint: true, destructiveHint: false, idempotentHint: true},
      },
      async (args) => {
        const result = await callBridge(name, args || {});
        return {
          content: [{type: 'text', text: JSON.stringify(result)}],
          structuredContent: result && typeof result === 'object' && !Array.isArray(result) ? result : {value: result},
        };
      },
    );
  }
  return server;
}

export function startStdio(options = {}) {
  return serveStdio(() => createServer(options), {legacy: 'reject'});
}

export async function createRuntime(options = {}) {
  const context = normalizeRuntimeContext(options.context || {});
  const session = options.session || createSession({
    ttlMs: options.sessionTtlMs,
    now: options.now,
    randomBytes: options.randomBytes,
  });
  const gateway = await startBridgeGateway({
    host: options.host || '127.0.0.1',
    port: options.port ?? 0,
    session,
    now: options.now,
    requestTimeoutMs: options.requestTimeoutMs,
    heartbeatTimeoutMs: options.heartbeatTimeoutMs,
    handshakeTimeoutMs: options.handshakeTimeoutMs,
  });
  const info = gateway.connectionInfo();
  const descriptor = Object.freeze({
    host: info.host,
    port: info.port,
    sessionId: info.sessionId,
    token: info.token,
    protocolVersion: info.protocolVersion,
    minecraftVersion: context.minecraftVersion,
    loader: context.loader,
    javaVersion: context.javaVersion,
    physicalProviders: context.physicalProviders.map((entry) => ({...entry})),
    activeProviderProfile: context.activeProviderProfile,
    mcpAuthorizedExtensionIds: [...context.mcpAuthorizedExtensionIds],
    heartbeatIntervalMs: options.heartbeatIntervalMs,
  });

  return Object.freeze({
    descriptor,
    callBridge: gateway.call,
    close: gateway.close,
  });
}

export async function startRuntime(options = {}) {
  const runtime = await createRuntime(options);
  const serveStdioFn = typeof options.serveStdioFn === 'function' ? options.serveStdioFn : startStdio;
  try {
    if (typeof options.onDescriptor === 'function') options.onDescriptor(runtime.descriptor);
    await serveStdioFn({callBridge: runtime.callBridge});
    return runtime;
  } finally {
    await runtime.close();
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  startRuntime({
    context: contextFromEnvironment(process.env),
    onDescriptor(descriptor) {
      console.error(`RPG_ASSET_MCP_ONE_TIME_DESCRIPTOR=${JSON.stringify(descriptor)}`);
    },
  }).catch((error) => {
    console.error(`Minecraft Mod Factory Asset MCP sidecar failed: ${String(error?.code || error?.message || error)}`);
    process.exitCode = 1;
  });
}
