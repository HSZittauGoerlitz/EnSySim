// external
use log::{debug, info, warn};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3_log::{Caching, Logger};
use numpy::PyReadonlyArrayDyn;
// local
#[macro_use]
// Environment
mod agent;
mod building;
mod cell;
// Components
mod controller;
mod boiler;
mod chp;
mod chp_system;
mod pv;
mod sep_bsl_agent;
mod storage_thermal;
// Misc
mod hist_memory;

#[pymodule]
#[allow(non_snake_case)] // for python binding
fn SystemComponentsFast(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    
    pyo3_log::init();

    m.add_class::<agent::Agent>()?;
    m.add_class::<building::Building>()?;
    m.add_class::<cell::Cell>()?;
    m.add_class::<sep_bsl_agent::SepBSLagent>()?;
    m.add_class::<pv::PV>()?;
    m.add_class::<chp_system::CHP_System>()?;
    m.add_function(wrap_pyfunction!(simulate, m)?).unwrap();
    Ok(())


}

/// Run Simulation with given models main cell
///
/// # Arguments
/// * main_cell (Cell): Main cell of energy system model
/// * steps (usize): Number of simulation steps to execute
/// * slp_phh (&f32): Standard load profile data for
///                             phh agents
/// * slp_bsla (&f32): Standard load profile data for
///                           agriculture business agents
/// * slp_bslc (&f32): Standard load profile data for
///                           common business agents
/// * hot_water_data (&f32): Hot water profile data
/// * t (&f32): Temperature curve
/// * eg (&f32): Global irradiation curve
#[pyfunction]
fn simulate(main_cell: &mut cell::Cell, steps: usize,
            slp_phh: PyReadonlyArrayDyn<f32>, slp_bsla: PyReadonlyArrayDyn<f32>,
            slp_bslc: PyReadonlyArrayDyn<f32>,
            hot_water_data: PyReadonlyArrayDyn<f32>,
            t: PyReadonlyArrayDyn<f32>, eg: PyReadonlyArrayDyn<f32>) {
    let mut slp: [f32; 3] = [0.; 3];

    let slp_phh = slp_phh.as_array();
    let slp_bsla = slp_bsla.as_array();
    let slp_bslc = slp_bslc.as_array();
    let hot_water_data = hot_water_data.as_array();
    let t = t.as_array();
    let eg = eg.as_array();

    // get the constant to a new memory place,
    //since cell can be changed due saving history
    let cell_t_out_n: f32 = main_cell.t_out_n;

    for step in 0..steps {
        slp[0] = slp_phh[step];
        slp[1] = slp_bsla[step];
        slp[2] = slp_bslc[step];
        main_cell.step(&slp, &hot_water_data[step], &t[step],
                       &cell_t_out_n, &eg[step]);
    }
}