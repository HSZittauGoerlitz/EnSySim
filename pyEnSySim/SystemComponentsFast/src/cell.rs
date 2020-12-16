// external
use pyo3::prelude::*;

use crate::{building, pv};

#[pyclass]
pub struct Cell {
    #[pyo3(get)]
    buildings: Vec<building::Building>,
    #[pyo3(get)]
    n_buildings: u32,
    #[pyo3(get)]
    eg: f32,
    #[pyo3(get)]
    pub t_out_n: f32,
    pv: Option<pv::PV>,
}

#[pymethods]
impl Cell {
    ///  Create cell to simulate a energy grid segment
    ///
    /// # Arguments
    /// * eg (f32): Mean annual global irradiation
    ///               for simulated region [kWh/m^2]
    /// * t_out_n (f32): Normed outside temperature for
    ///                  specific region in °C
    #[new]
    pub fn new(eg: f32, t_out_n: f32) -> Self {
        if eg < 0. {
            panic!("Mean annual global irradiation is a negative number")
        }

        let mut cell = Cell {
            buildings: Vec::new(),
            n_buildings: 0,
            eg: eg,
            t_out_n: t_out_n,
            pv: None,
        };

        cell
    }

    fn add_building(&mut self, building: building::Building) {
        self.buildings.push(building);
        self.n_buildings += 1;
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_cell_pv) => print!("WARNING: Cell already has a
                                     PV plant, nothing is added"),
        }
    }
}

/// PV plant
impl Cell {
    fn get_pv_generation(&self, eg: &f32) -> f32 {
        match &self.pv {
            None => 0.,
            Some(cell_pv) => {
                 cell_pv.step(eg)
            },
        }
    }

    /// Calculate and return current power balance
    ///
    /// # Arguments
    /// * slp_data (&[f32; 3]): Standard load Profile of all agent types
    /// * hw_profile (&f32): Actual hot water profile value [W]
    /// * t_out (&f32): Current (daily mean) outside temperature [°C]
    /// * t_out_n (&f32): Normed outside temperature for
    ///                   region of building [°C]
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * (f32, f32): Current electrical and thermal power balance [W]
    pub fn step(&self, slp_data: &[f32; 3], hw_profile: &f32,
            t_out: &f32, t_out_n: &f32, eg: &f32) -> (f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let mut thermal_load = 0.;
        let mut electrical_generation = 0.;
        let mut thermal_generation = 0.;
        let mut electrical_balance = 0.;
        let mut thermal_balance = 0.;

        // calculate loads
        for idx in 0..self.buildings.len() {
            let (sub_balance_e, sub_balance_t) = self.buildings[idx].
                                                    step(slp_data, hw_profile,
                                                         t_out, t_out_n, eg);
            electrical_load += sub_balance_e;
            thermal_load += sub_balance_t;
        }

        // calculate generation
        // TODO: CHP
        electrical_generation += self.get_pv_generation(eg);

        // TODO: Storage, Controller

        // Calculate resulting energy balance
        electrical_balance = electrical_generation - electrical_load;
        thermal_balance = thermal_generation - thermal_load;

        return (electrical_balance, thermal_balance);
    }
}