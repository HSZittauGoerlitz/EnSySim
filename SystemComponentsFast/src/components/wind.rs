// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Wind {
    h: f32,  // height of hub
    r: f32,  // radius (length) of blades
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Wind {
    ///  Create wind plant with specific hub height and blade radius
    ///
    /// # Arguments
    /// * ?
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(hist: usize) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8..=1.2) * coc * 1e3/eg * demand;


        let gen_e;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
        }

        let pv = PV {a: a,
                     gen_e: gen_e,
                    };
        pv
    }
}

/// wind plant
impl Wind {
    fn save_hist(&mut self, power_e: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*power_e)
            },
        }
    }

    /// Calculate current electrical power
    ///
    /// # Arguments
    /// * 
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self, eg: &f32) -> f32 {
        // calculate electrical power generated
        let power_e = ;

        // save data
        self.save_hist(&power_e);

        return power_e;
    }
}