// external
use pyo3::prelude::*;

use crate::components::boiler::Boiler;
use crate::components::chp::CHP;
use crate::components::tms_engine::TMSEngine;
use crate::components::generic_storage::GenericStorage;
use crate::misc::hist_memory;
use crate::misc::cell_manager::CellManager;
use crate::misc::ambient::AmbientParameters;


#[pyclass]
#[derive(Clone)]
pub struct CellTmsSystemThermalElectrical {
    #[pyo3(get)]
    chp: CHP,  // chp plant
    #[pyo3(get)]
    boiler: Boiler,  // peak load boiler (electric)
    #[pyo3(get)]
    tms_engine: TMSEngine,  //  tms engine
    #[pyo3(get)]
    pressure_tanks: GenericStorage,  // HP/LP pressure tanks of the tms system
    // Controller variables
    #[pyo3(get, set)]
    controller: Option<PyObject>,
    boiler_state: bool,
    chp_state: bool,
    tms_engine_charging_state: f32,
    tms_engine_discharging_state: f32,


    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CellTmsSystemThermalElectrical {
    /// Create thermal supply system for a cell,
    /// based on chp, boiler and thermal storage.
    ///
    /// # Arguments
    /// * p_th (f32): Thermal power of complete system [W]
    /// * chp_prop (f32): Proportion of chp on p_th
    /// * tms_prop (f32): Proportion of tms on p_th
    /// * tms_engine_pow_e(f32): Electrical nominal power of tms engine [W]
    /// * storage_cap (f32): Capacity of HP/LP tanks [Wh]
    /// * storage_self_loss (f32): Self loss HP/LP tanks [1/h]
    /// * storage_charge_eff (f32): HP/LP tanks charging efficiency [-]
    /// * storage_discharge_eff (f32): HP/LP tanks discharging efficiency [-]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(p_th: f32, chp_prop: f32, tms_engine_pow_e: f32,
               storage_cap: f32, storage_self_loss: f32,
               storage_charge_eff: f32, storage_discharge_eff: f32,
               hist: usize) -> Self
    {
        if p_th <= 0. {
            panic!("Thermal power of complete CHP system must be \
                    greater than 0")
        }

        let chp = CHP::new(chp_prop*p_th, hist);

        // boiler
        let boiler = Boiler::new((1. - chp_prop)*p_th, hist);

        let tms_engine = TMSEngine::new(tms_engine_pow_e, p_th,  hist);

        let pressure_tanks = GenericStorage::new(storage_cap,
                                          storage_charge_eff,
                                          storage_discharge_eff,
                                          storage_self_loss,
                                          2.*p_th,
                                          hist);
        
        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        }
        else {
            gen_e = None;
            gen_t = None;
        }

        CellTmsSystemThermalElectrical {chp,
                       boiler,
                       tms_engine,
                       pressure_tanks,
                       controller: None,
                       boiler_state: false,
                       chp_state: false,
                       tms_engine_charging_state: 0.,
                       tms_engine_discharging_state: 0.,
                       gen_e,
                       gen_t,
                       }
    }
}

impl CellTmsSystemThermalElectrical {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.3;
    const STORAGE_LEVEL_L: f32 = 0.2;
    const STORAGE_LEVEL_LL: f32 = 0.05;

    fn control(&mut self, thermal_demand: &f32, cell_pow_e_balance: &f32) {
        let storage_state = self.pressure_tanks.get_relative_charge();
        let cell_pow_t_balance = self.chp.pow_t + self.boiler.pow_t - thermal_demand;

        if storage_state <= CellTmsSystemThermalElectrical::STORAGE_LEVEL_LL {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= CellTmsSystemThermalElectrical::STORAGE_LEVEL_L) &
                !self.chp_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= CellTmsSystemThermalElectrical::STORAGE_LEVEL_H) &
                self.boiler_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= CellTmsSystemThermalElectrical::STORAGE_LEVEL_HH {
            self.chp_state = false;
            self.boiler_state = false;
        }
        
        if self.chp_state & self.boiler_state {
            let cell_pow_t_balance = self.chp.pow_t + self.boiler.pow_t - thermal_demand;
        } else if self.chp_state & !self.boiler_state {
            let cell_pow_t_balance = self.chp.pow_t - thermal_demand;
        } else if !self.chp_state & self.boiler_state {
            let cell_pow_t_balance = self.boiler.pow_t - thermal_demand;
        } else if !self.chp_state & !self.boiler_state {
            let cell_pow_t_balance = -thermal_demand;
        }

        let engine_nominal_full_pow_charge = (self.tms_engine.pow_e + self.tms_engine.pow_t)/self.tms_engine.compression_efficiency;
        let engine_nominal_full_pow_discharge = (self.tms_engine.pow_e + self.tms_engine.pow_t)/self.tms_engine.decompression_efficiency;
        let total_cell_balance = cell_pow_e_balance + cell_pow_t_balance;

        if (total_cell_balance > 0.) & (total_cell_balance > engine_nominal_full_pow_charge) {
            self.tms_engine_charging_state = 1.;
            self.tms_engine_discharging_state = 0.;
        } else if (total_cell_balance < 0.) & (-total_cell_balance > engine_nominal_full_pow_discharge) {
            self.tms_engine_charging_state = 0.;
            self.tms_engine_discharging_state = 1.;
        } else {
            self.tms_engine_charging_state = 0.;
            self.tms_engine_discharging_state = 0.;
        }

    }

    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * thermal_demand (&f32): Thermal power needed by dhn [W]
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power
    ///               and fuel used by system [W]
    pub fn step(&mut self, thermal_demand: &f32, cell_pow_e_balance: &f32, cell_state: &CellManager,
                amb: &AmbientParameters)
    -> (f32, f32, f32)
    {
        match &self.controller {
            None => self.control(thermal_demand, cell_pow_e_balance),
            Some(ctrl) => {
            },
        }

        let (pow_e, chp_t, chp_fuel) = self.chp.step(&self.chp_state);
        let (boiler_t, boiler_fuel) = self.boiler.step(&self.boiler_state);
        
        let cell_pow_t_balance = chp_t + boiler_t - thermal_demand;
        let pow_t = chp_t + boiler_t;

        //////////////////////////////////
        let (eng_pow_e, eng_pow_t, eng_con_e, eng_con_t) = self.tms_engine.step(&self.tms_engine_charging_state, &self.tms_engine_discharging_state);

        // call storage step -> check if all energy could be processed

        // charge/discharge for storage

        let mut storage_diff = 0.;

        if self.tms_engine_charging_state != 0. {
            let (storage_diff, _) =
            self.pressure_tanks.step(&((eng_pow_e + eng_pow_t)*self.tms_engine_charging_state));
        } else if self.tms_engine_discharging_state != 0. {
            let (storage_diff, _) =
            self.pressure_tanks.step(&-((eng_con_e + eng_con_t)*self.tms_engine_discharging_state));
        } else {
            let (storage_diff, _) =
            self.pressure_tanks.step(&0.);
        }

        // calculate thermal/electrical energy generation proportion for each part
        let prop_e = eng_pow_e/(eng_pow_e + eng_pow_t);
        let prop_t = 1. - prop_e;


        // save production data
        self.save_hist(&pow_e, &pow_t);

        // return supply data
        return (cell_pow_e_balance + storage_diff*prop_e, cell_pow_t_balance + storage_diff*prop_t, chp_fuel + boiler_fuel);
    }

    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*pow_e)
            },
        }
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }
}