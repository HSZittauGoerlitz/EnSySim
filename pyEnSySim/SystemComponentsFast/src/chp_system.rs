// external
use pyo3::prelude::*;
use rand::Rng;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct CHP_System {
    chp: CHP,  // chp plant
    storage: ThermalStorage,  // thermal storage

    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CHP_System {
    ///  Create CHP system with thermal storage and boiler
    ///  Parameters are power of CHP plant, power of peak load boiler and
    ///  capacity of thermal storage.
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * pow_e (f32): installed electrical chp power [W]
    /// * pow_t (f32): installed electrical chp power [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, hist: usize) -> Self {

        // chp:
        let pow_t = 0.3 * q_hln;
        let pow_e = 0.5 * pow_t;

        let state = false;

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C, c_water = 4.184 KJ(kg*K)
        let models = [200,300,400,500,600,750,950,1500,2000,3000,5000];


        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
        }

        let chp = CHP {pow_e: pow_e,
                     pow_t: pow_t,
                     state: state,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        chp
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
    pub fn step(&mut self, state: &bool) -> (f32, f32) {

        // save data
        self.save_hist_e(&pow_e);
        self.save_hist_t(&pow_t);

        return (pow_e, pow_t);
    }
}