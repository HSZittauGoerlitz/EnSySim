// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Solarthermal {
    a: f32,  // Effective Area of solarthermal plant [m^2]
    efficiency: f32, // simple effiency factor, TODO: curve
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
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

    /// TODO: change from electrical to thermal scaling
    #[new]
    pub fn new(eg: f32, coc: f32, demand: f32, hist: usize) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8..=1.2) * coc * 1e3/eg * demand;

        let efficiency: f32 = rng.gen_range(0.8..=0.9)

        let gen_t;

        if hist > 0 {
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_t = None;
        }

        let solarthermal = Solarthermal {a: a,
                     efficiency: efficiency,
                     gen_t: gen_t,
                    };
        solarthermal
    }
}

/// Solarthermal plant
impl Solarthermal {
    fn save_hist(&mut self, power_t: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*power_t)
            },
        }
    }

    /// Calculate current thermal power
    ///
    /// # Arguments
    /// * eg (&f32): Current irradiation on solarthermal module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting thermal power [W]

    /// TODO: Check type of irradiation to be used, depending on panel
    pub fn step(&mut self, eg: &f32) -> f32 {
        // calculate electrical power generated
        let power_t = self.a * eg * self.efficiency;

        // save data
        self.save_hist(&power_t);

        return power_t;
    }
}