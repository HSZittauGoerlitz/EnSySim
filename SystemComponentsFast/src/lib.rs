// external
use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use numpy::PyReadonlyArrayDyn;
// local
// Environment
mod environment;
// Entities
#[macro_use]
mod agent;
mod building;
mod cell;
// Components
mod controller;
mod boiler;
mod chp;
mod chp_system;
mod heatpump;
mod heatpump_system;
mod pv;
mod sep_bsl_agent;
mod generic_storage;
// Misc
mod helper;
mod hist_memory;

#[pymodule]
fn SystemComponentsFast(_py: Python<'_>, m: &PyModule) -> PyResult<()> {

    pyo3_log::init();

    m.add_class::<agent::Agent>()?;
    m.add_class::<building::Building>()?;
    m.add_class::<cell::Cell>()?;
    m.add_class::<sep_bsl_agent::SepBSLagent>()?;
    m.add_class::<pv::PV>()?;
    m.add_class::<heatpump_system::HeatpumpSystem>()?;
    m.add_class::<chp_system::ChpSystem>()?;
    m.add_function(wrap_pyfunction!(simulate, m)?).unwrap();
    Ok(())


}

/// Run Simulation with given models main cell
///
/// # Arguments
/// * main_cell (Cell): Main cell of energy system model
/// * steps (usize): Number of simulation steps to execute
/// * slp_phh (pyArr<f32>): Standard load profile data for
///                         phh agents
/// * slp_bsla (pyArr<f32>): Standard load profile data for
///                          agriculture business agents
/// * slp_bslc (pyArr<f32>): Standard load profile data for
///                          common business agents
/// * hot_water_data (pyArr<f32>): Actual hot water day profile factors [-]
/// * env_data (pyDict): All Environment/Weather data needed
///                      for the simulation
#[pyfunction]
fn simulate(main_cell: &mut cell::Cell, steps: usize,
            slp_phh: PyReadonlyArrayDyn<f32>, slp_bsla: PyReadonlyArrayDyn<f32>,
            slp_bslc: PyReadonlyArrayDyn<f32>,
            hot_water_data: PyReadonlyArrayDyn<f32>,
            env_data: HashMap<&str, Vec<f32>>) {
    let mut slp: [f32; 3] = [0.; 3];

    let slp_phh = slp_phh.as_array();
    let slp_bsla = slp_bsla.as_array();
    let slp_bslc = slp_bslc.as_array();
    let hot_water_data = hot_water_data.as_array();
    // Get Environment data and create object
    let mut env = environment::Environment::new(0., 0., 0., 0., 0.);
    let t = env_data.get("T [degC]").unwrap();
    let e_global = env_data.get("Eg [W/m^2]").unwrap();
    let e_diffuse = env_data.get("E diffuse [W/m^2]").unwrap();
    let e_direct = env_data.get("E direct [W/m^2]").unwrap();

    // get the constant to a new memory place,
    //since cell can be changed due saving history
    let cell_t_out_n: f32 = main_cell.t_out_n;

    for step in 0..steps {
        // set data for actual step
        // SLP
        slp[0] = slp_phh[step];
        slp[1] = slp_bsla[step];
        slp[2] = slp_bslc[step];
        // Environment
        env.t_out = t[step];
        env.irradiation_glob = e_global[step];
        env.irradiation_diff = e_diffuse[step];
        env.irradiation_dir = e_direct[step];
        main_cell.step(&slp, &hot_water_data[step], &cell_t_out_n, &env);
    }
}