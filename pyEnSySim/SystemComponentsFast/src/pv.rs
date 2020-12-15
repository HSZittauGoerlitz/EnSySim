// external
use pyo3::prelude::*;
use rand::Rng;

#[pyclass]
#[derive(Clone, Copy)]
pub struct PV {
    a: f32  // Effective Area of PV plant [m^2]
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
    #[new]
    pub fn new(eg: f32, coc: f32, demand: f32) -> Self {
        let mut rng = rand::thread_rng();

        let a = rng.gen_range(0.8, 1.2) * coc * 1e3/eg * demand;

        let pv = PV {a: a};
        pv
    }
}

/// PV plant
impl PV {
    /// Calculate current electrical power
    ///
    /// # Arguments
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&self, eg: &f32) -> f32 {
        return self.a * eg;
    }
}