// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Solarthermal {
    a: f32,  // Effective Area of solarthermal plant [m^2]
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Solarthermal {
    ///  Create solarthermal plant with specific Area
    ///
    /// # Arguments
    /// * eg (f32): Mean annual global irradiation
    ///             for simulated region [kWh/m^2]
    /// * coc (f32): Sum of all agents Coefficient of Consumer
    ///              of building corresponding to this solarthermal plant
    /// * demand (f32): Factor to describe the demand of agent(s)
    ///                 to cover their heating energy demand with solarthermal
    ///                 E.g demand = 1 means agent likes to cover his
    ///                 demand completely
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(eg: f32, coc: f32, demand: f32, hist: usize) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8..=1.2) * coc * 1e3/eg * demand;


        let gen_e;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
        }

        let solarthermal = Solarthermal {a: a,
                     gen_e: gen_e,
                    };
        solarthermal
    }
}

/// Solarthermal plant
impl Solarthermal {
    fn save_hist(&mut self, power_e: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*power_e)
            },
        }
    }

    /// Calculate current thermal power
    ///
    /// # Arguments
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting thermal power [W]
    pub fn step(&mut self, eg: &f32) -> f32 {
        // calculate electrical power generated
        let power_t = self.a * eg;

        // save data
        self.save_hist(&power_t);

        return power_t;
    }
}