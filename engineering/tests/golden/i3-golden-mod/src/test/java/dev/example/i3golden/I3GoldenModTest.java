package dev.example.i3golden;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class I3GoldenModTest {
    @Test
    void exposesCanonicalModId() {
        assertEquals("i3_golden_mod", I3GoldenMod.MOD_ID);
    }
}
