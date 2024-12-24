PY = python3

PCBDIR = .
FABS = oshpark jlcpcb
PCBS = NanoDD NanoProgrammer

FABDIR = Output
GRBDIR = Gerbers
DRCDIR = DRCs
FAILDIR = FailedDRCs

GRBDIRS = $(patsubst %,$(GRBDIR)/%,$(PCBS))
DIRS = $(PCBDIR) $(FABDIR) $(DRCDIR) $(FAILDIR) $(GRBDIRS)

.PHONY: all clean $(FABS)

all: $(FABS)

$(DIRS): %:
	mkdir -p $@

$(FABDIR)/%-oshpark.zip: $(DRCDIR)/%.rpt | $(FABDIR) $(GRBDIR)/%
	kikit fab oshpark $(PCBDIR)/$*/$*.kicad_pcb $(GRBDIR)/$*/
	mv $(GRBDIR)/$*/gerbers.zip $@

.SECONDARY:
.SECONDEXPANSION:
$(FABDIR)/%-jlcpcb.zip: $(DRCDIR)/%.rpt $$*/$$*.kicad_sch | $(FABDIR) $(GRBDIR)/%
	kikit fab jlcpcb $*/$*.kicad_pcb --assembly --missingError --schematic $*/$*.kicad_sch $(GRBDIR)/$*/
	cp $(GRBDIR)/$*/bom.csv $(FABDIR)/$*-bom-jlcpcb.csv
	cp $(GRBDIR)/$*/pos.csv $(FABDIR)/$*-pos-jlcpcb.csv
	mv $(GRBDIR)/$*/gerbers.zip $@

.SECONDARY:
.SECONDEXPANSION:
$(DRCDIR)/%.rpt: $(PCBDIR)/$$*/$$*.kicad_pcb | $(FAILDIR) $(DRCDIR)
	kikit drc run --ignoreExcluded $< > $(FAILDIR)/$*.rpt
	mv $(FAILDIR)/$*.rpt $@

$(FABS): %: $(patsubst %,$(FABDIR)/%-$$@.zip,$(PCBS))

clean:
	rm -rf $(DRCDIR) $(FAILDIR) $(GRBDIR) $(FABDIR)
