// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Boiler {
    #[pyo3(get)]
    pow_t: f32,  // installed power of boiler [W]
    state: bool,  // on/off switch for boiler

    #[pyo3(get)]
    efficiency: f32, // total efficiency of boiler 0 .. 1

    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    fuel_used: Option<hist_memory::HistMemory>
}

#[pymethods]
impl Boiler {
    ///  Create simple thermal boiler
    ///  Parameters are power of boiler
    ///
    /// # Arguments
    /// * pow (f32): installed thermal boiler power [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(pow: f32, hist: usize) -> Self {

        // boiler:
        let pow_t = pow;

        let state = false;

        let mut rng = rand::thread_rng();
        let efficiency: f32 = rng.gen_range(0.8..=0.9);

        let (gen_t, fuel_used) =
            if hist > 0 {
                (Some(hist_memory::HistMemory::new(hist)),
                 Some(hist_memory::HistMemory::new(hist)))
            } else {
                (None, None)
            };

        Boiler {pow_t,
                state,
                efficiency,
                gen_t,
                fuel_used
                }
    }

    pub fn set_efficiency(&mut self, efficiency: f32) {
        if (efficiency < 0.) | (efficiency > 1.) {
            panic!("Efficiency must be between 0 and 1");
        } else {
            self.efficiency = efficiency;
        }
    }
}

/// Boiler
impl Boiler {
    /// Calculate the fuel power needed to provide given thermal power.
    ///
    /// # Arguments
    /// * pow_t (f32): thermal power generated by boiler [W]
    ///
    /// # Returns
    /// f32: Power of fuel needed to provide given thermal power [W]
    pub fn get_fuel(&self, pow_t: &f32) -> f32 {
        pow_t / self.efficiency
    }

    fn save_hist_t(&mut self, pow_t: &f32, fuel_used: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
        match &mut self.fuel_used {
            None => {},
            Some(fuel_used_hist) => {
                fuel_used_hist.save(*fuel_used)
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
    pub fn step(&mut self, state: &bool) -> f32 {

        // update state
        self.state = *state;

        // calculate power output
        let pow_t;
        if self.state {
            pow_t = self.pow_t;
        }
        else {
            pow_t = 0.0;
        }

        // save and return data
        self.save_hist_t(&pow_t, &self.get_fuel(&pow_t));
        return pow_t;
    }
}