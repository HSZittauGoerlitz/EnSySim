// external
use pyo3::prelude::*;

use crate::boiler::Boiler;
use crate::chp::CHP;
use crate::storage_thermal::ThermalStorage;
use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
#[allow(non_snake_case)]  // for python binding
pub struct CHP_System {
    chp: CHP,  // chp plant
    storage: ThermalStorage,  // thermal storage
    boiler: Boiler,  // peak load boiler

    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
#[allow(non_snake_case)]  // for python binding
impl CHP_System {
    ///  Create CHP system with thermal storage and boiler
    ///  The technical design is based on norm heating load.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, hist: usize) -> Self {

        // chp:
        let pow_t = 0.3 * q_hln;
        let chp = CHP::new(pow_t, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C, c_water = 4.184 KJ(kg*K)
        let models: [f32;11] = [200.,300.,400.,500.,600.,750.,950.,1500.,2000.,3000.,5000.];
        let mut diffs: [f32;11] = [0.;11];
        let exact = 25.0 * 75.0; // kW * l/kW
    
    
        for (pos, model) in models.iter().enumerate() {
            diffs[pos] = (exact - model).abs();
        }
        
        let index = min_index(&diffs);
        // ToDo: bring to helper.rs file
        fn min_index(array: &[f32]) -> usize {
            let mut i = 0;
        
            for (j, &value) in array.iter().enumerate() {
                if value < array[i] {
                    i = j;
                }
            }
        
            i
        }
        let volume = models[index];
        let cap = volume * 4.184*1000. * 40.;

        let storage = ThermalStorage::new(cap, hist);

        // boiler
        let pow_t = 0.7 * q_hln;
        let boiler = Boiler::new(pow_t, hist);

        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } 
        else {
            gen_e = None;
            gen_t = None;
        }

        let chp_system = CHP_System {chp: chp,
                     storage: storage,
                     boiler: boiler,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        chp_system
    }
}

/// CHP plant
impl CHP_System {
    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*pow_e)
            },
        }
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }

    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of CHP plant (on/off)
    /// * thermal_load (&f32): thermal load of building this time step
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool, thermal_load: &f32) -> (f32, f32) {

        let time_step = 0.25; // ToDo: time step fixed

        // system satisfies heat demand from building
        // this is done by emptying storage
        // if state is true, system needs to actively produce heat
        // first chp is turned on and adds heat to storage, 
        // boiler only turns on, if this is not enough 
        // excess heat is destroyed
        // ToDo: add partial load to chp and boiler
        // ToDo: check if chp does not over supply system -> boiler

        let(pow_e, mut pow_t) = self.chp.step(&state);

        if *state == false {
            let _result = self.boiler.step(&state);
        }
        else {
            // stored enough?
            if (pow_t + self.storage.get_charge()/time_step) >= *thermal_load {
                // turn boiler off this step
                self.boiler.step(&false);
            }
            else {
                // turn boiler on this step
                pow_t += self.boiler.step(&true);
            }
        }

        // save production data
        self.save_hist(&pow_e, &pow_t);
        
        // get thermal load from storage and update charging state
        pow_t = self.storage.step(&pow_t, thermal_load);

        // return supply data
        return (pow_e, pow_t);
    }
}