PLAYDATE_SDK_PATH ?= $(HOME)/playdate
PDC ?= $(PLAYDATE_SDK_PATH)/bin/pdc
LUA ?= lua5.4
PDX := ZnomeKop.pdx

.PHONY: all art build test preview clean run

all: build

## Regenerate every sprite sheet and the Lua tile atlas.
art:
	python3 tools/gen_art.py

## Compile source/ into the .pdx bundle.
build:
	PLAYDATE_SDK_PATH=$(PLAYDATE_SDK_PATH) $(PDC) source $(PDX)

## Headless tests for generation, battle and data integrity.
test:
	$(LUA) tests/run.lua

## ASCII dump of a generated sector: make preview SECTOR=3 SEED=42
SECTOR ?= 2
SEED ?= 12345
preview:
	$(LUA) tools/preview_map.lua $(SECTOR) $(SEED)

run: build
	$(PLAYDATE_SDK_PATH)/bin/PlaydateSimulator $(PDX)

clean:
	rm -rf $(PDX)
