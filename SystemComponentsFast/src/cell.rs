// external
use pyo3::prelude::*;
use log::{warn};

use crate::{building, pv, sep_bsl_agent, hist_memory, save_e, save_t};

#[pyclass]
#[derive(Clone)]
pub struct Cell {
    #[pyo3(get)]
    sub_cells: Vec<Cell>,
    #[pyo3(get)]
    buildings: Vec<building::Building>,
    #[pyo3(get)]
    sep_bsl_agents: Vec<sep_bsl_agent::SepBSLagent>,
    #[pyo3(get)]
    n_cells: u32,
    #[pyo3(get)]
    n_buildings: u32,
    #[pyo3(get)]
    n_sep_bsl_agents: u32,
    #[pyo3(get)]
    eg: f32,
    #[pyo3(get)]
    pub t_out_n: f32,
    #[pyo3(get)]
    pv: Option<pv::PV>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_t: Option<hist_memory::HistMemory>,
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
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(eg: f32, t_out_n: f32, hist: usize) -> Self {
        if eg < 0. {
            panic!("Mean annual global irradiation is a negative number")
        }

        let (gen_e, gen_t, load_e, load_t);

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
            load_e = Some(hist_memory::HistMemory::new(hist));
            load_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
            load_e = None;
            load_t = None;
        }

        let cell = Cell {
            sub_cells: Vec::new(),
            n_cells: 0,
            buildings: Vec::new(),
            n_buildings: 0,
            sep_bsl_agents: Vec::new(),
            n_sep_bsl_agents: 0,
            eg: eg,
            t_out_n: t_out_n,
            pv: None,
            gen_e: gen_e,
            gen_t: gen_t,
            load_e: load_e,
            load_t: load_t,
        };

        cell
    }

    fn add_building(&mut self, building: building::Building) {
        self.buildings.push(building);
        self.n_buildings += 1;
    }

    fn update_building(&mut self, building_idx: usize,
                       building: building::Building) {
        self.buildings[building_idx] = building;
    }

    fn add_cell(&mut self, cell:Cell) {
        self.sub_cells.push(cell);
        self.n_cells += 1;
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_cell_pv) => warn!("Cell already has a
                                     PV plant, nothing is added"),
        }
    }

    fn add_sep_bsl_agent(&mut self,
                         sep_bsl_agent: sep_bsl_agent::SepBSLagent) {
        self.sep_bsl_agents.push(sep_bsl_agent);
        self.n_sep_bsl_agents += 1;
    }

    fn replace_building(&mut self, building_pos: usize,
                        building: building::Building)
    {
        if building_pos > (self.n_buildings - 1) as usize {
            warn!("Building position exceeds number of available buildings. \
                   Max. possiblie building position is {}",
                   self.n_buildings - 1);
        } else {
            self.buildings[building_pos] = building;
        }
    }
}

/// PV plant
impl Cell {
    fn get_pv_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.pv {
            None => 0.,
            Some(cell_pv) => {
                 cell_pv.step(eg)
            },
        }
    }

    /// Calculate and return current power consumption and generation
    ///
    /// # Arguments
    /// * slp_data (&[f32; 3]): Standard load Profile of all agent types
    /// * hw_profile (&f32): Actual hot water day profile factor [-]
    /// * t_out (&f32): Current (daily mean) outside temperature [°C]
    /// * t_out_n (&f32): Normed outside temperature for
    ///                   region of building [°C]
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * (f32, f32, f32, f32): Current electrical and thermal
    ///                         power consumption and generation [W]
    pub fn step(&mut self, slp_data: &[f32; 3], hw_profile: &f32,
                t_out: &f32, t_out_n: &f32, eg: &f32) -> (f32, f32, f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let mut thermal_load = 0.;
        let mut electrical_generation = 0.;
        let mut thermal_generation = 0.;

        // calculate sub cells
        self.sub_cells.iter_mut().for_each(|sc: &mut Cell| {
            let (sub_gen_e, sub_load_e, sub_gen_t, sub_load_t) =
                sc.step(slp_data, hw_profile,
                        t_out, t_out_n, eg);
            electrical_generation += sub_gen_e;
            thermal_generation += sub_gen_t;
            electrical_load += sub_load_e;
            thermal_load += sub_load_t;
        });

        // calculate buildings
        self.buildings.iter_mut().for_each(|b: &mut building::Building| {
            let (sub_gen_e, sub_load_e, sub_gen_t, sub_load_t) =
                b.step(slp_data, hw_profile,
                       t_out, eg);
            electrical_generation += sub_gen_e;
            thermal_generation += sub_gen_t;
            electrical_load += sub_load_e;
            thermal_load += sub_load_t;
        });

        // calculate separate BSL agents
        self.sep_bsl_agents.iter_mut().
            for_each(|sbsl: &mut sep_bsl_agent::SepBSLagent| {
                let (sub_gen_e, sub_load_e) =
                    sbsl.step(slp_data, eg);
                electrical_generation += sub_gen_e;
                electrical_load += sub_load_e;
        });


        // calculate generation
        // TODO: CHP
        electrical_generation += self.get_pv_generation(eg);

        // TODO: Storage, Controller

        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation, thermal_load);

        return (electrical_generation, electrical_load,
                thermal_generation, thermal_load);
    }
}