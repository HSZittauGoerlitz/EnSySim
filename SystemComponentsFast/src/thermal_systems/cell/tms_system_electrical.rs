// external
use pyo3::prelude::*;

use crate::components::tms_engine::TMSEngine;
use crate::components::generic_storage::GenericStorage;
use crate::misc::hist_memory;
use crate::misc::cell_manager::CellManager;
use crate::misc::ambient::AmbientParameters;


#[pyclass]
#[derive(Clone)]
pub struct CellTmsSystemThermal {
    #[pyo3(get)]
    tms_engine: TMSEngine,  // tms engine
    #[pyo3(get)]
    pressure_tanks: GenericStorage,  // the pressure tanks, storage of the tms system

    // Controller variables
    #[pyo3(get, set)]
    controller: Option<PyObject>,
    tms_engine_charging_state: f32,
    tms_engine_discharging_state: f32,


    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CellTmsSystemThermal {
    /// Create electrical supply system for a cell,
    /// based on cell electrical power balance and a tms system.
    ///
    /// # Arguments
    /// * tms_engine_pow_e(f32): Electrical nominal power of tms engine [W]
    /// * p_el(f32): Electrical capacity needed for the system
    /// * storage_cap (f32): Capacity of storage [Wh]
    /// * storage_self_loss (f32): Self loss storage [1/h]
    /// * storage_charge_eff (f32): Storage charging efficiency [-]
    /// * storage_discharge_eff (f32): Storage discharging efficiency [-]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(tms_engine_pow_e: f32, p_el: f32,
               storage_cap: f32, storage_self_loss: f32,
               storage_charge_eff: f32, storage_discharge_eff: f32,
               hist: usize) -> Self
    {
        let tms_engine = TMSEngine::new(tms_engine_pow_e, 0., hist);

        let pressure_tanks = GenericStorage::new(storage_cap,
                                          storage_charge_eff,
                                          storage_discharge_eff,
                                          storage_self_loss,
                                          p_el,
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

        CellTmsSystemThermal {tms_engine,
                       pressure_tanks,
                       controller: None,
                       tms_engine_charging_state: 0.,
                       tms_engine_discharging_state: 0.,
                       gen_e,
                       gen_t,
                       }
    }
}

impl CellTmsSystemThermal {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.3;
    const STORAGE_LEVEL_L: f32 = 0.2;
    const STORAGE_LEVEL_LL: f32 = 0.05;

    fn control(&mut self, cell_power_balance: &f32) {

        let storage_state = self.pressure_tanks.get_relative_charge();

        if cell_power_balance > &(self.tms_engine.pow_e/self.tms_engine.compression_efficiency) {
            self.tms_engine_charging_state = 1.;
            self.tms_engine_discharging_state = 0.;
        } else if cell_power_balance > &(self.tms_engine.pow_e/self.tms_engine.decompression_efficiency) {
            self.tms_engine_charging_state = 1.;
            self.tms_engine_discharging_state = 0.;
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
    pub fn step(&mut self, cell_power_balance: &f32, cell_state: &CellManager,
                amb: &AmbientParameters)
    -> (f32, f32)
    {
        match &self.controller {
            None => self.control(cell_power_balance),
            Some(ctrl) => {  // Supposedly a control file here
            },
        }

        // engine step
        let (pow_e, pow_t, con_e, con_t) = self.tms_engine.step(&(self.tms_engine_charging_state), &(self.tms_engine_discharging_state));
        
        // call storage step -> check if all energy could be processed

        let mut storage_diff = 0.;

        // charge/discharge for storage
        if self.tms_engine_charging_state != 0. {
            let (storage_diff, _) =
            self.pressure_tanks.step(&(pow_e*self.tms_engine_charging_state));
        } else if self.tms_engine_discharging_state != 0. {
            let (storage_diff, _) =
            self.pressure_tanks.step(&(-con_e*self.tms_engine_discharging_state));
        } else {
            let (storage_diff, _) =
            self.pressure_tanks.step(&0.);
        }

        // save production data
        self.save_hist(&pow_e, &pow_t);

        // return supply data
        return (cell_power_balance + storage_diff, pow_t);
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