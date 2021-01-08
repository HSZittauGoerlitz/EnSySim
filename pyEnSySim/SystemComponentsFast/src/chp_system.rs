// external
use pyo3::prelude::*;

use crate::boiler;
use crate::chp;
use crate::storage_thermal;
use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct CHP_System {
    chp: CHP,  // chp plant
    storage: ThermalStorage,  // thermal storage
    boiler: Boiler,  // peak load boiler

    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CHP_System {
    ///  Create CHP system with thermal storage and boiler
    ///  The technical design is based on norm heating load.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, hist: usize) -> Self {

        // chp:
        let pow_t = 0.3 * q_hln;
        let chp = chp::CHP::new(pow_t, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C, c_water = 4.184 KJ(kg*K)
        let models = [200,300,400,500,600,750,950,1500,2000,3000,5000];
        let volume = 500; // ToDo: closest value
        let cap = volume * 4.184*1000 * 40;

        let storage = storage_thermal::ThermalStorage::new(cap, hist);

        // boiler
        let pow_t = 0.7 * q_hln;
        let boiler = boiler::Boiler::new(pow_t, hist);

        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
        }

        let chp_system = CHP_System {chp: chp,
                     storage: storage,
                     boiler: boiler,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        chp_system
    }
}

/// CHP plant
impl CHP {
    fn save_hist_e(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*pow_e)
            },
        }
    }
    fn save_hist_t(&mut self, pow_t: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }
    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of CHP plant (on/off)
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool, thermal_load: &f32) -> (f32, f32) {

        if state == false {
            self.chp.step(state);
            self.boiler.step(state);
            let pow_e = 0;
        }
        else {
            // run chp with full power
            let (pow_e, pow_t) = self.chp.step(state);
            // charge storage
            self.storage.charge(pow_t);
            // stored enough?
            if pow_t+self.storage.temp_charge/time_step >= thermal_load { //ToDo: time step
                // turn boiler off this step
                self.boiler.step(false);
            }
            else {
                // turn boiler on this step
                let pow_t = self.boiler.step(true);
                self.storage.charge(pow_t);
            }
        // get thermal load from storage and update charging state
        let pow_t = self.storage.step(thermal_load);

        // save data
        self.save_hist_e(&pow_e);
        self.save_hist_t(&pow_t);

        return (pow_e, pow_t);
    }
}