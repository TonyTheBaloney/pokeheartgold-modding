#include "config.h"
	.include "macros.inc"
	.include "overlay_112.inc"
	.include "global.inc"

	.public gPokewalkerIrLink
	.public gPokewalkerIrPacket
	.public gPokewalkerIrPayload

	.bss

gPokewalkerIrLink:
	.space 0x38

gPokewalkerIrPacket:
	.space 0x8

gPokewalkerIrPayload:
	.space 0x84
