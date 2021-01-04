// external
use pyo3::prelude::*;
use rand::Rng;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct CHP {
    pow_t: f32,  // installed power of chp plant [kW]
    pow_e: f32,  // electrical power of chp plant [kW]
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CHP {
    ///  Create CHP with thermal storage 
    ///  Parameters are power of CHP plant, power of peak load boiler and
    ///  capacity of thermal storage.
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * pow (f32): installed chp power [kW]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(pow_t: f32, hist: usize) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8, 1.2) * coc * 1e3/eg * demand;


        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
        }

        let chp = CHP {pow: pow,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        pv
    }
}

/// CHP plant
impl CHP {
    fn save_hist_e(&mut self, power_e: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*power_e)
            },
        }
    }
    fn save_hist_t(&mut self, power_t: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*power_t)
            }
        }
    }
    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self, state: &f32) -> f32 {
        // calculate electrical power generated
        let power_e = self.a * eg;
        let power_t = 

        // save data
        self.save_hist_e(&power_e);
        self.save_hist_t(&power_t);

        return (power_e, power_t);
    }
}