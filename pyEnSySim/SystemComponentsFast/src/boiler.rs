// external
use pyo3::prelude::*;
use rand::Rng;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Boiler {
    pow_t: f32,  // installed power of chp plant [W]
    state: bool,  // on/off switch for boiler
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Boiler {
    ///  Create simple thermal boiler
    ///  Parameters are power of boiler
    ///
    /// # Arguments
    /// * pow_t (f32): installed electrical chp power [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(pow: f32, hist: usize) -> Self {

        // boiler:
        let pow_t = pow_t;

        let gen_t;

        if hist > 0 {
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_t = None;
        }

        let boiler = Boiler {pow_e: pow_e,
                     pow_t: pow_t,
                     state: state,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        boiler
    }
}

/// Boiler
impl Boiler {
    fn save_hist_t(&mut self, pow_t: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }
    /// Calculate current thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of boiler (on/off)
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool) -> (f32, f32) {

        // update state
        let self.state = state;
        // calculate power output
        let pow_t = self.state as f32 * self.pow_t;

        // save data
        self.save_hist_t(&pow_t);

        return pow_t;
    }
}