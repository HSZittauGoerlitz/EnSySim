// external
use pyo3::prelude::*;
use rand::Rng;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct PV {
    a: f32,  // Effective Area of PV plant [m^2]
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl PV {
    ///  Create PV plant with specific Area
    ///
    /// # Arguments
    /// * eg (f32): Mean annual global irradiation
    ///               for simulated region [kWh/m^2]
    /// * coc (f32): Sum of all agents Coefficient of Consumer
    ///               of building corresponding to this PV plant
    /// * demand (f32): Factor to describe the demand of agent(s)
    ///                   to cover their electrical energy demand with PV
    ///                   E.g demand = 1 means agent likes to cover his
    ///                   demand completely
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(eg: f32, coc: f32, demand: f32, hist: usize) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8, 1.2) * coc * 1e3/eg * demand;


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

/// PV plant
impl PV {
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