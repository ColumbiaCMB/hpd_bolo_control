## This class compensates for the 2-wire measurement 
# On the board - We really should have done a 4-wire on 
# the SSA out but this is the "fudge"
# This class needs access to a bolo_board class
# As that is where it get's it's settings from
# We allow a change in wire_resistance for tweeking real_time
# But the rest you need to edit this class
# We currently correct for only the SSA but we need the whole system
from numpy import array


class resistance_compensator:
    def __init__(self, bolo_board,wire_resistance=19.5):
        #We setup all the know resistances in here
        self.bb = bolo_board
        self.setup_resitances(wire_resistance)

        #And set some flags for what we want to correct for
        self.correct_SSA_bias = True
        self.correct_SSA_fb = True
        self.correct_S2_bias = False
        self.correct_S2_fb = False
        self.correct_S1_bias = False
        self.correct_S1_fb = False
        self.correct_tes_bias = False

    def setup_resitances(self,wire_resistance):
        self.R_wire = wire_resistance
        self.SSA_int_res_single = 4.7 #Single bank resistance
        self.R_SSA_int = self.SSA_int_res_single/6.0 #six banks in parallel

        self.n_gnd_wires = 4 #We have four returns
        self.R_gnd = self.R_wire/self.n_gnd_wires

        self.R_SSA_bias = 30.1e3 #Just the bias resister
        self.R_SSA_fb = 24.9e3 + 1e3 #Bias plus 1k internal
        
        self.G_amp = 22.0 #amplifier gain

        #Some useful totals
        self.R_SSA_bias_total = self.R_SSA_bias +self. R_SSA_int + self.R_wire +self.R_gnd
        self.R_SSA_fb_total = self.R_SSA_fb + self.R_gnd
        self.R_SSA_bias_internal = self.R_wire + self.R_gnd
        self.R_SSA_fb_internal = self.R_gnd

    ## This takes the current recorded values
    # In the bolo_board registers and provides 
    # A corrected voltage
    def correct_voltage(self,v):
        return v - self.calculate_static_drop()

    def calculate_static_drop(self):
        vdrop = 0
        if  self.correct_SSA_bias is True:
             vdrop = vdrop + self.calculate_SSA_bias_drop()
        if self.correct_SSA_fb is True:
            vdrop = vdrop +  self.calculate_SSA_fb_drop()

        return vdrop

    def calculate_SSA_bias_drop(self):
        vin = self.bb.registers["ssa_bias_voltage"]
        current = vin/self.R_SSA_bias_total
        v_drop = self.G_amp*self.R_SSA_bias_internal*current
        return v_drop

    def calculate_SSA_fb_drop(self):
        vin = self.bb.registers["ssa_fb_voltage"]
        current = vin/self.R_SSA_fb_total
        v_drop = self.G_amp*self.R_SSA_fb_internal*current
        return v_drop

    ## When we sweep we probably want to 
    # not correct on the fly but correct an array
    # of values dependent upon what we are sweeping
    # This of course has to assume that the only thing
    # changing is the sweep voltage and nothing else
    def correct_batch_voltage(self,v_source,v,line):
        if line == "ssa_bias":
            state = self.correct_SSA_bias
            self.correct_SSA_bias = False
            current = array(v_source)/self.R_SSA_bias_total
            v_drop = self.G_amp*self.R_SSA_bias_internal*current
            v_corrected = array(v)-v_drop-self.calculate_static_drop()
            self.correct_SSA_bias = state
        if line == "self_fb":
            state = self.correct_SSA_fb
            self.correct_SSA_fb = False
            current = array(v_source)/self.R_SSA_fb_total
            v_drop = self.G_amp*self.R_SSA_fb_internal*current
            v_corrected = array(v)-v_drop-self.calculate_static_drop()
            self.correct_SSA_fb = True

        return v_corrected
     
        
