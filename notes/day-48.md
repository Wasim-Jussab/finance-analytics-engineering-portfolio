# Day 48 — make the evidence pack portable

The verified pack still pointed at working files in different directories. That was enough to check the current checkout, but awkward to hand to a reviewer or retain as one unit. I added a content-addressed directory that copies the exact indexed bytes alongside the pack and a separate bundle manifest.

Creation checks the recorded pack ID, safe relative paths, byte sizes and fingerprints before copying anything. It writes through a temporary directory and renames only after every artifact is present. Verification starts from the finished bundle, checks every copied byte and rejects missing or additional files without referring back to the originals.

I chose an inspectable directory rather than a compressed archive because the dataset is small and transparency matters more than storage efficiency here. The bundle is still local and editable by anyone with filesystem access. It demonstrates portable, tamper-evident evidence at inspection time, not immutable retention, authorship or external attestation.
