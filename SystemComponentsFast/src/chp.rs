// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct CHP {
    pow_e: f32,  // electrical power of chp plant [W]
    pow_t: f32,  // installed power of chp plant [W]
    state: bool,  // on/off switch for chp plant

    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl CHP {
    ///  Create CHP plant
    ///  Parameters are power of CHP plant
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * pow_t (f32): installed electrical chp power [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(power_t: f32, hist: usize) -> Self {

        if power_t < 0. {
            panic!("Installed thermal power of chp \
                    must be greater than 0")
        }

        // chp:
        let pow_t = power_t;
        let pow_e = 0.5 * pow_t;

        let state = false;

        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
        }

        CHP {pow_e: pow_e,
             pow_t: pow_t,
             state: state,
             gen_e: gen_e,
             gen_t: gen_t,
             }
    }
}

/// CHP plant
impl CHP {
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
    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of CHP plant (on/off)
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool) -> (f32, f32) {

        // update state
        self.state = *state;

        // calculate power output
        let pow_t;
        let pow_e;
        if self.state {
            pow_t = self.pow_t;
            pow_e = self.pow_e;
        }
        else {
            pow_t = 0.0;
            pow_e = 0.0;
        }

        // save and return data
        self.save_hist(&pow_e, &pow_t);

        return (pow_e, pow_t);
    }
}