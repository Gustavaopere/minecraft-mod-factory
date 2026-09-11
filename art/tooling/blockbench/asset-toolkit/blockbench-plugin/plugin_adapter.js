'use strict';

const core = require('../core/index.js');
const modeling = require('./modeling_adapter.js');
const uvTexture = require('./uv_texture_adapter.js');
const animation = require('./animation_adapter.js');
const geckolib4 = require('./geckolib4_adapter.js');
const azurelib3 = require('./azurelib3_adapter.js');
const neoforgeNativeAnimation = require('./neoforge_native_animation_adapter.js');
const easyModelEntities = require('./easy_model_entities_adapter.js');
const emfCem = require('./emf_cem_adapter.js');
const animatedJava = require('./animated_java_adapter.js');

function registerBlockbenchPlugin(bb) {
  let auditAction = null;
  let profileAction = null;
  let modelingMutationAction = null;
  let uvTextureMutationAction = null;
  let animationMutationAction = null;
  let bridgeConnectAction = null;
  let bridgeDisconnectAction = null;
  let bridgeStatusAction = null;
  let bridgeRuntime = null;

  function show(result) {
    bb.Blockbench.showMessageBox({
      title: 'Minecraft Mod Factory Asset Toolkit',
      icon: result.errors.length ? 'error' : 'check_circle',
      message: core.formatReport(result),
      buttons: ['OK'],
    });
  }

  function showError(title, error) {
    const code = error && typeof error.code === 'string' ? error.code : 'TOOLKIT_ERROR';
    const detail = error && typeof error.message === 'string' ? error.message : String(error);
    bb.Blockbench.showMessageBox({
      title,
      icon: 'error',
      message: `${code}: ${detail}`.slice(0, 2048),
      buttons: ['OK'],
    });
  }

  function showBridgeError(error) {
    showError('Minecraft Mod Factory Asset Toolkit — Live Bridge', error);
  }

  function addToolAction(action) {
    bb.MenuBar.menus.tools.addAction(action);
    return action;
  }

  bb.Plugin.register('rpg_asset_toolkit', {
    title: 'Minecraft Mod Factory Asset Toolkit',
    author: 'Gustavaopere',
    description: 'Structural/provider-aware asset QA with bounded local modeling/rig, UV/texture, and generic animation mutations plus an optional authenticated read-only desktop-local MCP Live Bridge.',
    icon: 'fact_check',
    version: '0.6.0',
    min_version: '5.1.6',
    variant: 'both',
    tags: ['Minecraft: Java Edition'],
    onload() {
      auditAction = addToolAction(new bb.Action('rpg_asset_toolkit_validate', {
        name: 'Validate RPG Asset',
        description: 'Run read-only structural checks on the active Blockbench project.',
        icon: 'fact_check',
        click() { show(core.validateProject(bb.Blockbench.Project, {})); },
      }));
      profileAction = addToolAction(new bb.Action('rpg_asset_toolkit_validate_profile', {
        name: 'Validate RPG Asset Against Contract Profile',
        description: 'Run the same checks plus optional required bones/animations/maxSpan from JSON.',
        icon: 'rule',
        click() {
          bb.Blockbench.textPrompt('RPG Asset Contract Profile (JSON)', '{}', (text) => {
            try { show(core.validateProject(bb.Blockbench.Project, core.parseProfileJson(text))); }
            catch (error) { showError('Minecraft Mod Factory Asset Toolkit — Invalid Profile', error); }
          });
        },
      }));

      if (bb.Blockbench.isWeb === false) {
        modelingMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_modeling_mutation_batch', {
          name: 'Apply RPG Modeling/Rig Batch',
          description: 'Apply a bounded declarative modeling/rig batch locally with expected-revision checks, preflight, Undo, and rollback. This does not expose remote MCP writes.',
          icon: 'architecture',
          click() {
            try {
              const adapter = modeling.createBlockbenchModelingAdapter(bb);
              const template = JSON.stringify({
                expectedRevision: adapter.getRevision(),
                dryRun: true,
                label: 'Minecraft Mod Factory Asset Toolkit Modeling/Rig Batch',
                operations: [],
              }, null, 2);
              bb.Blockbench.textPrompt('RPG Modeling/Rig Mutation Batch (JSON)', template, (text) => {
                try {
                  const result = core.applyMutationBatch(adapter, JSON.parse(text));
                  bb.Blockbench.showMessageBox({
                    title: 'Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch',
                    icon: 'check_circle',
                    message: JSON.stringify(result, null, 2).slice(0, 4096),
                    buttons: ['OK'],
                  });
                } catch (error) {
                  showError('Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch Failed', error);
                }
              });
            } catch (error) {
              showError('Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch Unavailable', error);
            }
          },
        }));

        uvTextureMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_uv_texture_batch', {
          name: 'Apply RPG UV/Texture Batch',
          description: 'Apply bounded declarative UV and deterministic texture-pixel mutations locally with expected-revision checks, dry-run preflight, bitmap-aware Undo, and rollback. This does not expose remote MCP writes.',
          icon: 'texture',
          click() {
            try {
              const adapter = uvTexture.createBlockbenchUvTextureAdapter(bb);
              const template = JSON.stringify({
                expectedRevision: adapter.getRevision(),
                dryRun: true,
                label: 'Minecraft Mod Factory Asset Toolkit UV/Texture Batch',
                operations: [],
              }, null, 2);
              bb.Blockbench.textPrompt('RPG UV/Texture Mutation Batch (JSON)', template, (text) => {
                try {
                  const result = core.applyUvTextureBatch(adapter, JSON.parse(text));
                  bb.Blockbench.showMessageBox({
                    title: 'Minecraft Mod Factory Asset Toolkit — UV/Texture Batch',
                    icon: 'check_circle',
                    message: JSON.stringify(result, null, 2).slice(0, 4096),
                    buttons: ['OK'],
                  });
                } catch (error) {
                  showError('Minecraft Mod Factory Asset Toolkit — UV/Texture Batch Failed', error);
                }
              });
            } catch (error) {
              showError('Minecraft Mod Factory Asset Toolkit — UV/Texture Batch Unavailable', error);
            }
          },
        }));

        animationMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_animation_batch', {
          name: 'Apply RPG Generic Animation Batch',
          description: 'Apply bounded provider-neutral animation/keyframe mutations locally with expected-revision checks, preflight, Undo, and rollback. Provider-specific effect-marker serialization remains unavailable here and remote MCP stays read-only.',
          icon: 'animation',
          click() {
            try {
              const adapter = animation.createBlockbenchAnimationAdapter(bb);
              const template = JSON.stringify({
                expectedRevision: adapter.getRevision(),
                dryRun: true,
                label: 'Minecraft Mod Factory Asset Toolkit Generic Animation Batch',
                operations: [],
              }, null, 2);
              bb.Blockbench.textPrompt('RPG Generic Animation Mutation Batch (JSON)', template, (text) => {
                try {
                  const result = core.applyAnimationBatch(adapter, JSON.parse(text));
                  bb.Blockbench.showMessageBox({
                    title: 'Minecraft Mod Factory Asset Toolkit — Generic Animation Batch',
                    icon: 'check_circle',
                    message: JSON.stringify(result, null, 2).slice(0, 4096),
                    buttons: ['OK'],
                  });
                } catch (error) {
                  showError('Minecraft Mod Factory Asset Toolkit — Generic Animation Batch Failed', error);
                }
              });
            } catch (error) {
              showError('Minecraft Mod Factory Asset Toolkit — Generic Animation Batch Unavailable', error);
            }
          },
        }));

        bridgeConnectAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_connect', {
          name: 'Connect Minecraft Mod Factory Asset MCP (Read-only)',
          description: 'Connect this desktop Blockbench session to the authenticated numeric-loopback Minecraft Mod Factory Asset MCP sidecar.',
          icon: 'link',
          click() {
            bb.Blockbench.textPrompt('Minecraft Mod Factory Asset MCP Connection Descriptor (JSON)', '{}', async (text) => {
              try {
                if (bridgeRuntime) await bridgeRuntime.connection.disconnect();
                const liveBridge = require('./live_bridge_adapter.js');
                const runtime = liveBridge.createBlockbenchLiveBridgeRuntime(bb, text);
                await runtime.connection.connect();
                bridgeRuntime = runtime;
                bb.Blockbench.showQuickMessage?.('Minecraft Mod Factory Asset MCP read-only bridge connected', 2500);
              } catch (error) {
                bridgeRuntime = null;
                showBridgeError(error);
              }
            });
          },
        }));

        bridgeDisconnectAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_disconnect', {
          name: 'Disconnect Minecraft Mod Factory Asset MCP',
          description: 'Disconnect the current read-only local bridge session.',
          icon: 'link_off',
          async click() {
            try {
              if (bridgeRuntime) await bridgeRuntime.connection.disconnect();
              bridgeRuntime = null;
              bb.Blockbench.showQuickMessage?.('Minecraft Mod Factory Asset MCP bridge disconnected', 2000);
            } catch (error) {
              bridgeRuntime = null;
              showBridgeError(error);
            }
          },
        }));

        bridgeStatusAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_status', {
          name: 'Minecraft Mod Factory Asset MCP Bridge Status',
          description: 'Show non-secret connection state for the local read-only bridge.',
          icon: 'info',
          click() {
            const status = bridgeRuntime ? bridgeRuntime.connection.status() : {connected: false, generation: 0, capabilities: []};
            bb.Blockbench.showMessageBox({
              title: 'Minecraft Mod Factory Asset Toolkit — Live Bridge Status',
              icon: status.connected ? 'check_circle' : 'info',
              message: JSON.stringify(status, null, 2),
              buttons: ['OK'],
            });
          },
        }));
      }
    },
    onunload() {
      if (bridgeRuntime) {
        try { void bridgeRuntime.connection.disconnect(); } catch (_) { /* best effort during plugin unload */ }
      }
      bridgeRuntime = null;
      for (const action of [
        auditAction,
        profileAction,
        modelingMutationAction,
        uvTextureMutationAction,
        animationMutationAction,
        bridgeConnectAction,
        bridgeDisconnectAction,
        bridgeStatusAction,
      ]) {
        if (action) action.delete();
      }
      auditAction = null;
      profileAction = null;
      modelingMutationAction = null;
      uvTextureMutationAction = null;
      animationMutationAction = null;
      bridgeConnectAction = null;
      bridgeDisconnectAction = null;
      bridgeStatusAction = null;
    },
  });
}

module.exports = {
  registerBlockbenchPlugin,
  createBlockbenchModelingAdapter: modeling.createBlockbenchModelingAdapter,
  createBlockbenchUvTextureAdapter: uvTexture.createBlockbenchUvTextureAdapter,
  createBlockbenchAnimationAdapter: animation.createBlockbenchAnimationAdapter,
  createBlockbenchGeckoLib4Adapter: geckolib4.createBlockbenchGeckoLib4Adapter,
  createBlockbenchAzureLib3Adapter: azurelib3.createBlockbenchAzureLib3Adapter,
  createBlockbenchNeoForgeNativeAnimationAdapter: neoforgeNativeAnimation.createBlockbenchNeoForgeNativeAnimationAdapter,
  createBlockbenchEasyModelEntitiesAdapter: easyModelEntities.createBlockbenchEasyModelEntitiesAdapter,
  createBlockbenchEmfCemAdapter: emfCem.createBlockbenchEmfCemAdapter,
  createBlockbenchAnimatedJavaAdapter: animatedJava.createBlockbenchAnimatedJavaAdapter,
};
