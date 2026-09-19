I10 physical multiplayer acceptance package — MANUAL STARTUP

Manual startup is the default. This package intentionally does not contain a
START-I10-MULTIPLAYER.bat or START-I10-MULTIPLAYER.sh that launches everything.

Windows:
1. Run START-I10-SERVER.bat and wait for the dedicated server to report Done.
2. In that dedicated server console run:
   forceload add 159 160 161 160
3. In the same server console run:
   i10probe baseline
4. The baseline line must be exactly equivalent to:
   validation=VALID runtime=UNFORMED revision=0 sentinel=empty count=0 capability=false last_known_formed=false
5. Run START-I10-CLIENT-A.bat.
6. Run START-I10-CLIENT-B.bat.

Linux/macOS:
1. Run ./START-I10-SERVER.sh and wait for the dedicated server to report Done.
2. Run the same forceload and i10probe baseline commands in the server console.
3. Run ./START-I10-CLIENT-A.sh.
4. Run ./START-I10-CLIENT-B.sh.

Each wrapper starts exactly one process through run-i10-manual-process.py.
The helper keeps Gradle isolated under .i10-gradle-user-home and writes the
canonical server/client process logs and metadata under:
  build/i10-multiplayer-acceptance/

The helper does not form the multiblock, break it, reconnect Client B, create
canonical screenshots, or mark the gate PASS. Physical formation and visual
observations remain required by the acceptance protocol.

After both clients are online, follow engineering/tests/i10-multiplayer-acceptance.md:
- both clients observe UNFORMED;
- Client A alone forms through normal interaction;
- both observe FORMED;
- break one required casing from the server console with i10probe break_required_part;
- both observe UNFORMED;
- disconnect Client B completely;
- start START-I10-CLIENT-B.bat again to reconnect B while A stays connected;
- verify B receives the current UNFORMED state.

Do not use i10probe setup for the multiplayer baseline. i10probe baseline is the
dedicated deterministic acceptance command and must be used from a fresh physical
artifact built from the exact commit recorded in I10-SOURCE-COMMIT.txt.
