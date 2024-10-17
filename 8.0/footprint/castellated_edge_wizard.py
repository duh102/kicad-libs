from __future__ import division
import pcbnew

import FootprintWizardBase as FPWbase
import PadArray as PA

class CastellatedEdgeWizard(FPWbase.FootprintWizard):
    catParams = 'Parameters'
    # number of pins in this footprint, min 1
    keyNumPins = 'Pin Count'
    # whether (true) or not (false) to include a backup throughhole behind the castellated edge; placed using pad depth (so pad depth becomes center to center of the plated holes)
    keyBackupTH = 'Create Backup Through-holes'
    # pitch between pins, default 2mm
    keyPinPitch = 'Pin Pitch'
    # diameter of the drill, typically 0.2mm larger than largest diameter of mating pin
    keyDrillDiameter = 'Drill Diameter'
    # diameter of the plated area of the throughhole, typically hole diameter + 0.55mm
    keyPadSize = 'Through-hole Pad Diameter'
    # length of the rectangular plated area beyond the pad, measured from the center of the hole, typically same as pitch
    keyPadDepth = 'Extra Pad Depth'

    def GetName(self):
        return "Castellated Edge Wizard"

    def GetDescription(self):
        return "Wizard to build castellated edge arrays, incorporating just the edge or also a backup throughhole pad inside the board outline"

    def GenerateParameterList(self):
        self.AddParam(self.catParams, self.keyBackupTH, self.uBool, True) # default to using the backup pad
        self.AddParam(self.catParams, self.keyNumPins, self.uInteger, 2) # default two pads (to show what multiple pads looks like)

        # Typical 2mm pitch settings
        self.AddParam(self.catParams, self.keyPinPitch, self.uMM, 2.0)
        self.AddParam(self.catParams, self.keyDrillDiameter, self.uMM, 0.8)
        self.AddParam(self.catParams, self.keyPadSize, self.uMM, 1.35)
        self.AddParam(self.catParams, self.keyPadDepth, self.uMM, 2.0)

    def CheckParameters(self):
        pass

    def GetValue(self):
        pad_count = self.parameters[self.catParams][self.keyNumPins]
        pin_pitch = pcbnew.ToMM(self.parameters[self.catParams][self.keyPinPitch])
        uses_backup = '_backup' if self.parameters[self.catParams][self.keyBackupTH] else ''
        return 'PinHeader_1x{pads:02d}_P{pitch:0.2f}mm_Castellated{backup:s}'.format(pads=pad_count, pitch=pin_pitch, backup=uses_backup)

    def GetModDescription(self):
        pad_count = self.parameters[self.catParams][self.keyNumPins]
        pin_pitch = pcbnew.ToMM(self.parameters[self.catParams][self.keyPinPitch])
        uses_backup = ', with backup' if self.parameters[self.catParams][self.keyBackupTH] else ''
        return 'Through hole straight pin header, 1x{pins:02d}, {pitch:0.2f}mm pitch, single row{backup:s}'.format(pins=pad_count, pitch=pin_pitch, backup=uses_backup)

    def GetModKeywords(self):
        pad_count = self.parameters[self.catParams][self.keyNumPins]
        pin_pitch = pcbnew.ToMM(self.parameters[self.catParams][self.keyPinPitch])
        return 'Through hole pin header THT 1x{pins:02d}, {pitch:0.2f}mm single row'.format(pins=pad_count, pitch=pin_pitch)

    def GetPad(self):
        padLength = self.parameters["Pads"][self.padLengthKey]
        padWidth  = self.parameters["Pads"][self.padWidthKey]
        return PA.PadMaker(self.module).SMDPad(
            padLength, padWidth, shape=pcbnew.PAD_SHAPE_RECT)

    def BuildThisFootprint(self):
        # Retrieve all the parameters
        pad_count = self.parameters[self.catParams][self.keyNumPins]
        pin_pitch = self.parameters[self.catParams][self.keyPinPitch] # in mm
        drill_diameter = self.parameters[self.catParams][self.keyDrillDiameter] # in mm
        pad_size = self.parameters[self.catParams][self.keyPadSize] # in mm
        pad_depth = self.parameters[self.catParams][self.keyPadDepth] # in mm
        uses_backup = self.parameters[self.catParams][self.keyBackupTH]

        # Set the module parameters
        self.module.SetValue(self.GetValue())
        self.module.SetLibDescription(self.GetModDescription())
        self.module.SetKeywords(self.GetModKeywords())
        self.module.SetAttributes(pcbnew.FP_THROUGH_HOLE)

        # The 1st throughhole is always a rectangle
        pad_1 = PA.PadMaker(self.module).THPad(pad_size, pad_size, drill=drill_diameter, shape=pcbnew.PAD_SHAPE_RECT)
        # Subsequent throughholes are circular
        pad_2 = PA.PadMaker(self.module).THPad(pad_size, pad_size, drill=drill_diameter, shape=pcbnew.PAD_SHAPE_CIRCLE)
        # The extra pad area is formed with SMD pads
        pad_extra = PA.PadMaker(self.module).SMDPad(pad_size, pad_depth, shape=pcbnew.PAD_SHAPE_RECT)

        # Front extra pad layerset
        front_ls = pcbnew.LSET(pcbnew.F_Mask)
        front_ls.AddLayer(pcbnew.F_Cu)
        # Back version of the same
        back_ls = pcbnew.LSET(pcbnew.B_Mask)
        back_ls.AddLayer(pcbnew.B_Cu)

        # Dimensional help
        pad_extra_x_offset = int(pad_depth/2.0)
        half_pitch = int(pin_pitch/2.0)
        edge_offset = pcbnew.FromMM(0.5) # mm, how far from the edge to stop silkscreening
        courtyard_offset = pad_size/2.0+pcbnew.FromMM(0.4) # mm, how far from the edge of the throughhole pads to consider the courtyard
        corner_size = pcbnew.FromMM(0.5) # mm, how large of a corner to make in the top left of the footprint

        # Reference lines etc
        silk_thickness = pcbnew.FromMM(0.12)
        reference_thickness = pcbnew.FromMM(0.05)
        text_size = pcbnew.FromMM(1.0)

        # Courtyard
        self.draw.SetLayer(pcbnew.F_CrtYd)
        self.draw.SetLineThickness(reference_thickness)

        court_x0 = (-pad_extra_x_offset) if uses_backup else int((-pad_depth+(pad_size/2))/2.0)
        court_y0 = int((pad_count-1)*pin_pitch/2.0)
        court_w = int(courtyard_offset*2 + (pad_depth if uses_backup else pad_depth/2.0+(pad_size-drill_diameter)/2.0))
        court_h = (pad_count-1)*pin_pitch + courtyard_offset*2

        self.draw.Box(court_x0, court_y0, court_w, court_h)

        # Reference and value
        text_offset = -(text_size+courtyard_offset)

        self.draw.Value(-pad_extra_x_offset, text_offset-text_size*3, text_size)
        self.draw.Reference(-pad_extra_x_offset, text_offset-text_size, text_size)

        # Silkscreen outline
        ss_left = -(pad_depth+courtyard_offset)
        pads_size = (pad_count-1)*pin_pitch
        self.draw.SetLayer(pcbnew.F_SilkS)
        self.draw.SetLineThickness(silk_thickness)
        self.draw.Polyline([(-edge_offset, -courtyard_offset),
                            (ss_left+corner_size, -courtyard_offset),
                            (ss_left, -courtyard_offset+corner_size),
                            (ss_left, pads_size+courtyard_offset),
                            (-edge_offset, pads_size+courtyard_offset)])

        # Draw the pads
        ## Pads will extend downward (+y) from 0, pad 1 will be on 0,0
        ## If there are backup pads, they will be to the left (-x) from their matching castellated pads
        for i in range(pad_count):
            pinNum = i+1
            thPad = pad_1 if pinNum == 1 else pad_2
            y = i * pin_pitch
            mainPad = pcbnew.PAD(thPad)
            topEx = pcbnew.PAD(pad_extra)
            topEx.SetLayerSet(front_ls)
            bottomEx = pcbnew.PAD(pad_extra)
            bottomEx.SetLayerSet(back_ls)

            mainPad.SetPosition(pcbnew.VECTOR2I(0, y))
            mainPad.SetNumber(pinNum)
            topEx.SetPosition(pcbnew.VECTOR2I(-pad_extra_x_offset, y))
            topEx.SetNumber(pinNum)
            bottomEx.SetPosition(pcbnew.VECTOR2I(-pad_extra_x_offset, y))
            bottomEx.SetNumber(pinNum)
            self.module.Add(mainPad)
            self.module.Add(topEx)
            self.module.Add(bottomEx)

            if uses_backup:
                backupPad = pcbnew.PAD(thPad)
                backupPad.SetPosition(pcbnew.VECTOR2I(-pad_depth, y))
                backupPad.SetNumber(pinNum)
                self.module.Add(backupPad)


CastellatedEdgeWizard().register()
