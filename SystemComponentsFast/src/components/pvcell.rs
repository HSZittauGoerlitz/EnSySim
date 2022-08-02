// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct PVCell {
    a: f32,  // Effective Area of PV plant [m^2]
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl PVCell {
    ///  Create PV plant with specific Area
    ///
    /// # Arguments
    ///
    /// # For building:
    /// * eg (f32): Mean annual global irradiation
    ///             for simulated region [kWh/m^2]
    /// * hist (usize): Size of history memory (0 for no memory)
    ///
    /// # For cell:
    /// * a: Effective Area of PV plant [m^2]
    /// * hist (usize): Size of history memory (0 for no memory)
    ///
    ///
    ///


    #[new]
    pub fn new(eg: f32, a: f32, hist: usize) -> Self {

        let gen_e;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
        }

        let pvcell = PVCell {a: a,
                     gen_e: gen_e,
                    };
        PVCell}
}

impl PVCell {
    ///PV plant
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
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self, eg: &f32) -> f32 {
        // calculate electrical power generated
        let power_e = self.a * eg;

        // save data
        self.save_hist(&power_e);

        return power_e;
    }
}