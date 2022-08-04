// external
use pyo3::prelude::*;
use log::{error};
use rand::Rng;
use rand_distr::{Distribution, FisherF, Gamma};

use crate::save_e;
use crate::components::{pv};
use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct SepBSLagent {
    a_type: usize,  // 1: BSLa, 2: BSLc
    #[pyo3(get)]
    coc: f32,
    #[pyo3(get)]
    demand_apv: f32,
    #[pyo3(get)]
    pv: Option<pv::PV>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl SepBSLagent {
    /// Create separate business Agent
    ///
    /// # Arguments
    /// * a_type (usize): Type of agent (1: BSLa, 2: BSLc)
    ///
    ///                   "BSLa": Agriculture business with
    ///                           electrical standard load profile and
    ///                           thermal phh standard load profile
    ///                   "BSLc": Common business with
    ///                           electrical standard load profile and
    ///                           thermal phh standard load profile
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(a_type: usize, hist: usize) -> Self {
        if a_type == 0 {
            panic!("Separate BSL agents must not be PHH agents");
        } else if a_type > 2 {
            panic!("Unknown agent type");
        }

        let (gen_e, load_e);

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            load_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            load_e = None;
        }

        let mut agent = SepBSLagent {a_type: a_type,
                                     coc: 0.,
                                     demand_apv: 0.,
                                     pv: None,
                                     gen_e: gen_e,
                                     load_e: load_e,
                                     };
        agent.get_apv_demand();
        agent.get_coc();
        agent
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_sep_bsl_pv) => error!("Separate BSL agent already \
                                        has a PV plant, nothing is added"),
        }
    }

    /// Add PV with dimensioning of installed PV power
    /// by agents demand statistics
    /// and environments global irradiation history.
    ///
    /// # Arguments
    /// * Eg (f32): Mean annual global irradiation
    ///             for simulated region [kWh/m^2]
    /// * hist (usize): Size of history memory for pv plant (0 for no memory)
    fn add_dimensioned_pv(&mut self, eg: f32, hist: usize) {
            Some(_sep_bsl_pv) => error!("Separate BSL agent already \
                                        has a PV plant, nothing is added"),
        }
    }
}

/// Agent to simulate electrical profile of bigger business
impl SepBSLagent {
    pub fn coc(&self) -> &f32 {
        &self.coc
    }

    /// Calculate the demand for PV area to cover a part of the
    /// electrical energy consumption, using BSL statistics.
    fn get_apv_demand(&mut self) {
        let mut rng = rand::thread_rng();

        self.demand_apv = rng.gen_range(0.8..=1.2);

        let dist = FisherF::new(7.025235971695065, 2205.596792511838).unwrap();
        self.demand_apv *= dist.sample(&mut rng) * 0.299704041191481 + 0.1;
    }

    /// Get COC factor of agent
    /// Use BSL statistics
    fn get_coc(&mut self) {
        let mut coc: f32 = 0.;
        let mut rng = rand::thread_rng();

        // Gamma sistribution with shape, scale
        let dist = Gamma::new(1.399147113755027, 1.876519590091970).unwrap();
        sample_coc!(dist, rng, coc, 1.);

        if coc < 1. {
            self.coc = 1.;
        } else {
            self.coc = coc;
        }
    }

    fn get_pv_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.pv {
            None => 0.,
            Some(sep_bsl_pv) => {
                sep_bsl_pv.step(eg)
            },
        }
    }

    /// Calculate and return current power consumption and generation
    ///
    /// # Arguments
    /// * slp_data (&[f32; 3]): Standard load Profile of all agent types
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * (f32, f32): Current electrical power balance [W]
    pub fn step(&mut self, slp_data: &[f32; 3], eg: &f32) -> (f32, f32) {
        let mut rng = rand::thread_rng();
        // init current step
        let mut electrical_load = 0.;
        let mut electrical_generation = 0.;

        // calculate load
        electrical_load += slp_data[self.a_type] * rng.gen_range(0.8..=1.2);

        // calculate generation
        // TODO: CHP
        electrical_generation += self.get_pv_generation(eg);

        // TODO: Storage, Controller

        // save data
        save_e!(self, electrical_generation, electrical_load);

        return (electrical_generation, electrical_load);
    }
}