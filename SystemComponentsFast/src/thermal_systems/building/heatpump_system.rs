// external
use pyo3::prelude::*;
use log::{info};

use crate::misc::helper::{find_heating_system_storage,
                          find_heat_storage_loss_parameter,
                          find_minimum};

use crate::components::boiler::Boiler;
use crate::components::heatpump::Heatpump;
use crate::components::generic_storage::GenericStorage;
use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct BuildingHeatpumpSystem {
    #[pyo3(get)]
    heatpump: Heatpump,  // heatpump
    #[pyo3(get)]
    storage: GenericStorage,  // thermal storage
    #[pyo3(get)]
    boiler: Boiler,  // peak load boiler

    // Controller variables
    boiler_state: bool,
    hp_state: f32,
    control_mode: u8,  // 0: Winter, 1: Intermediate, 2: Summer
    // Hysteresis for control mode in relation to buildings lim. Temp.
    t_heat_lim_h: f32,  // degC
    // save storage losses, to consider in temperature control
    last_losses: f32,  // W

    #[pyo3(get)]
    con_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

fn average(numbers: &[f32]) -> f32 {
    let mut average: f32 = numbers.iter().sum();
    average = average / numbers.len() as f32;
    average
}

fn average_bool_select_weighted(numbers: &[f32], weights: &[f32],
                                bool_select: &[bool]) -> f32 {
    let mut sum = 0.;
    let mut weights_sum = 0.;
    for (idx, sel) in bool_select.iter().enumerate() {
        if *sel {
            sum += numbers[idx] * weights[idx];
            weights_sum += weights[idx];
        }
    }
    sum  / weights_sum
}

fn cop_from_coefficients(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {

    let coeffs_cop;
    if pow_t < &18000. {
        if t_out < &7. {
            coeffs_cop = [5.398, -0.05601, 0.14818, -0.00185, 0., 0.0008];}
        else if t_out < &10. {
            coeffs_cop = [6.22734, -0.07497, 0.07841, 0., 0., 0.];}
        else {
            coeffs_cop = [5.59461, -0.0671, 0.17291, -0.00097, 0., -0.00206];}
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_cop = [4.79304, -0.04132, 0.05651, 0., 0., 0.];}
        else if t_out < &10. {
            coeffs_cop = [6.34439, -0.1043, 0.0751, -0.00016, 0.00059, 0.];}
        else {
            coeffs_cop = [5.07629, -0.04833, 0.09969, -0.00096, 0.00009, 0.];}
    }
    else {
        if t_out < &7. {
            coeffs_cop = [6.28133, -0.10087, 0.11251, -0.00097, 0.00056,
                          0.00069];}
        else if t_out < &10. {
            coeffs_cop = [6.23384, -0.09963, 0.11295, -0.00061, 0.00052, 0.];}
        else {
            coeffs_cop = [5.0019, -0.04138, 0.10137, -0.00112, 0., 0.00027];}
    }
    let cop = coeffs_cop[0] + coeffs_cop[1]*t_supply
              + coeffs_cop[2]*t_out + coeffs_cop[3]*t_supply*t_out
              + coeffs_cop[4]*f32::powf(*t_supply,2.)
              + coeffs_cop[5]*f32::powf(*t_out, 2.);
    cop
}

fn q_from_coefficients(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {

    let coeffs_q;
    if pow_t < &18000. {
        if t_out < &7. {
            coeffs_q = [1.04213, -0.00234, 0.03152, -0.00019, 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [1.02701, -0.00366, 0.03202, 0.00003, 0., 0.];}
        else {
            coeffs_q = [0.81917, -0.00301, 0.0651, -0.00003, 0., -0.00112];}
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_q = [1.03825, -0.00223, 0.02272, 0., 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [0.93526, -0.0005, 0.03926, -0.00021, 0., 0.];}
        else {
            coeffs_q = [0.79796, 0.00005, 0.05928, -0.00026, 0., -0.00066];}
    }
    else {
        if t_out < &7. {
            coeffs_q = [1.10902, -0.00478, 0.02136, 0.00019, 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [1.08294, -0.00438, 0.03386, 0., 0., 0.];}
        else {
            coeffs_q = [1.10262, -0.00316, 0.0295, -0.00009, 0., 0.00008];}
    }
    let q = coeffs_q[0] + coeffs_q[1]*t_supply
              + coeffs_q[2]*t_out + coeffs_q[3]*t_supply*t_out
              + coeffs_q[4]*f32::powf(*t_supply,2.)
              + coeffs_q[5]*f32::powf(*t_out, 2.);
    q
}

#[pymethods]
impl BuildingHeatpumpSystem {
    ///  Create heatpump system with thermal storage and boiler
    ///  The technical design is based on norm heating load.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building [W]
    /// * seas_perf_fac (f32): minimum allowed seasonal performance factor,
    ///                        dependent on building (3.5 or 4.5)
    /// * t_supply (f32): supply temperature, dependent on building [°C]
    /// * t_ref (Vec<[f32; 365]>): temperatures of reference year
    ///                            (DWD, 1995-2012) [°C]
    /// * t_heat_lim (f32): average outside temperature over which heating
    ///                     will suppply, building specific [°C]
    /// * t_out_n (f32): norm outside temperature [°C]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, seas_perf_fac: f32, t_supply: f32,
               t_ref: Vec<f32>, t_heat_lim: f32, t_out_n: f32,
               hist: usize) -> Self {

        // ToDo: account for drinking water heating time
        // ?account for blocking times in final result

        // start with full building supply
        // use 6h blocking time by electricity provider
        let mut pow_t = q_hln * 24. / (24.-6.) /
                        cop_from_coefficients(&q_hln, &t_out_n, &t_supply);

        // local copy neccessary
        let reference_temperatures = t_ref.to_vec();

        // get heating days bools (hourly)
        let mut heating_days: [bool; 8760] = [false; 8760];
        for i in 0..=364 {
            // ToDo: idx created twice
            let idx = (i*24)..(i*24+24);
            let t_day = &reference_temperatures[idx];
            let idx = (i*24)..(i*24+24);
            if average(t_day) < t_heat_lim {
                heating_days[idx].fill(true);
            }
        }

        // Q-intercept of heating line (at 0°C)
        let intercept = (t_heat_lim / (t_heat_lim - t_out_n)) * q_hln;
        // slope of heating line
        let slope = q_hln / (t_out_n - t_heat_lim);

        // calculate COP and power factor for all 'true' hours in heating days
        let mut cops: [f32; 8760] = [0.; 8760];
        let mut qs: [f32; 8760] = [0.; 8760];
        // needed heating power for each hour
        let mut pow_heat: [f32; 8760] = [0.; 8760];
        for (idx, t_out) in reference_temperatures.iter().enumerate() {
            if t_out > &t_heat_lim {
                heating_days[idx] = false;
            }
            if heating_days[idx] {
                cops[idx] = cop_from_coefficients(&pow_t, &t_out, &t_supply);
                qs[idx] = q_from_coefficients(&pow_t, &t_out, &t_supply);
                // calculate needed heating power for this hour
                pow_heat[idx] = (-q_hln / (t_heat_lim-t_out_n)) *
                                t_out + intercept;
            }
        }

        // get minimum temperature from reference year
        let mut t_min = find_minimum(&reference_temperatures);

        // introduce seasonal performance factor as mean of COPS
        let mut cop_mean = -1.;

        // introduce weights to take into account over- and undersupply
        // during this hour
        let weights: [f32; 8760] = [1.; 8760];

        // increase lower bound of heatpump working temperatures till mean
        // COP satisfies minimum seasonal performance factor
        let mut iter_count = 0.;
        while cop_mean < seas_perf_fac {

            if t_min >= t_heat_lim {
                panic!("Heatpump minimum operating temperature must be greater
                        then minimum heating temperature of building.
                        Apparantly cop was choosen too high.")
            }
            // increase lower bound of heatpump working temperature
            if iter_count > 0. {
                t_min = t_min + 1.;
            }
            // update bool vector for hour selection
            for (idx, temp) in reference_temperatures.iter().enumerate() {
                if *temp < t_min {
                    heating_days[idx] = false;
                }
            }

            // calculate installed heatpump power based on heat needed at
            //  minimum working temperature and power factor
            pow_t = (slope * t_min + intercept) /
                    q_from_coefficients(&pow_t, &t_min, &t_supply);
            if pow_t < 1000. {
                panic!("For this building heatpump cannot be configured.
                       Try decreasing minimum cop.")
            }
            // calculate weights
/*             for (idx, value) in heating_days.iter().enumerate() {
                let div;
                if *value == true {
                    div = pow_heat[idx] / (pow_t * qs[idx]);

                    if div > 1. {
                        weights[idx] = 1.;
                    }
                    else {
                        weights[idx] = div;
                    }
                }
            } */
            // calculate mean cop
            cop_mean = average_bool_select_weighted(&cops, &weights,
                                                    &heating_days);
            iter_count += 1.;
        }

        pow_t = pow_t * 24. / (24. - 6.);

        // create heatpump
        let heatpump = Heatpump::new(pow_t, t_supply, t_min, hist);

        // create boiler based on norm heating load
        // --> bivalent-alternative
        let boiler = Boiler::new(q_hln, hist);

        // thermal storage:
        // 50l~kg per kW thermal generation, 40K difference -> 60°C
        // 5°C spread, 20°C room temperature
        let temp_diff = t_supply + 5. - 20.;
        let (cap, volume) = find_heating_system_storage(&pow_t, &temp_diff);
        let self_loss = find_heat_storage_loss_parameter(&volume, &cap);

        // make sure storage can handle max power from heatpump, 20°C used
        let max_q = q_from_coefficients(&pow_t, &20., &t_supply);
        // dummy parameters for now
        let storage = GenericStorage::new(cap,
                                          0.95,
                                          0.95,
                                          self_loss,
                                          pow_t*max_q + q_hln,
                                          hist);

        let con_e;
        let gen_t;

        if hist > 0 {
            con_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        }
        else {
            con_e = None;
            gen_t = None;
        }

        info!("
               designed heatpump system with following specifications
               after {} iterations:
               heatpump nominal power: {:.2}kW
               predicted mean cop: {:.2}
               minimal working temperature: {:.2}°C
               storage capacity: {:.2}kWh
               boiler nominal power: {:.2}kW",
               iter_count,
               pow_t/1000.,
               cop_mean,
               t_min,
               cap/1000.,
               q_hln/1000.);

        BuildingHeatpumpSystem {heatpump,
                        storage,
                        boiler,
                        boiler_state: false,
                        hp_state: 0.,
                        control_mode: 1,
                        t_heat_lim_h: 2.,
                        last_losses: 0.,
                        con_e,
                        gen_t}
    }
}


impl BuildingHeatpumpSystem {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.2;
    const STORAGE_LEVEL_L: f32 = 0.05;
    const STORAGE_LEVEL_LL: f32 = 0.01;

    fn control(&mut self){
        match self.control_mode {
            0 => self.winter_mode(),
            1 => self.intermediate_mode(),
            2 => self.summer_mode(),
            _ => panic!("Unknown control mode {} of heat pump system",
                        self.control_mode),
        }
    }

    pub fn get_losses(&self) -> &f32 {
        &self.last_losses
    }

    fn intermediate_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();

        if self.boiler_state {self.boiler_state = false;}

        if storage_state <= BuildingHeatpumpSystem::STORAGE_LEVEL_LL {
            self.hp_state = 1.;
        } else if storage_state > BuildingHeatpumpSystem::STORAGE_LEVEL_H {
            self.hp_state = 0.;
        }
    }

    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.con_e {
            None => {},
            Some(con_e) => {
                con_e.save(*pow_e)
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
    /// * heating_demand (&f32): Thermal power needed for
    ///                          heating the building [W]
    /// * hot_water_demand (&f32): Thermal power needed by agents for
    ///                            warm water [W]
    /// * t_out (&f32): Outside temperature [degC]
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, heating_demand: &f32, hot_water_demand: &f32,
        t_out: &f32, t_heat_lim: &f32, t_out_mean: &f32) -> (f32, f32)
    {
        // TODO: respect minimal working temperature of heatpump
        self.update_control_mode(t_heat_lim, t_out_mean);
        self.control();

        let (con_e, hp_t) = self.heatpump.step(&self.hp_state, t_out);
        let boiler_t = self.boiler.step(&self.boiler_state);

        let thermal_load = heating_demand + hot_water_demand;

        let pow_t = hp_t + boiler_t;
        let storage_t = pow_t - thermal_load;

        // call storage step -> check if all energy could be processed
        let (storage_diff, storage_loss) = self.storage.step(&storage_t);

        self.last_losses = storage_loss;

        // save production data
        self.save_hist(&con_e, &pow_t);

        // return supply data
        return (-con_e, thermal_load + storage_diff + storage_loss);
    }

    fn summer_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();

        if self.boiler_state {self.boiler_state = false;}

        if storage_state <= BuildingHeatpumpSystem::STORAGE_LEVEL_LL {
            self.hp_state = 0.2;
        } else if storage_state > BuildingHeatpumpSystem::STORAGE_LEVEL_L {
            self.hp_state = 0.0;
        }
    }

    /// Change Control mode
    ///
    /// 0: Winter
    /// 1: Intermediate
    /// 2: Summer
    ///
    /// # Arguments
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    fn update_control_mode(&mut self, t_heat_lim: &f32, t_out_mean: &f32)
    {
        // Get actual control mode
        match self.control_mode {
            0 => {
                if *t_out_mean > (*t_heat_lim - 0.8*self.t_heat_lim_h) {
                    self.control_mode = 1;
                }
            },
            1 => {
                if *t_out_mean > (*t_heat_lim + 1.2*self.t_heat_lim_h) {
                    self.control_mode = 2;
                }
                else if *t_out_mean < (*t_heat_lim - 1.2*self.t_heat_lim_h) {
                    self.control_mode = 0;
                }
            },
            2 => {
                if *t_out_mean < (*t_heat_lim + 0.8*self.t_heat_lim_h) {
                    self.control_mode = 1;
                }
            },
            _ => panic!("Unknown control mode {} of heat pump system",
                        self.control_mode),
        }
    }

    fn winter_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();

        if storage_state <=BuildingHeatpumpSystem::STORAGE_LEVEL_LL {
            self.boiler_state = true;
            self.hp_state = 1.;
        }

        if storage_state > BuildingHeatpumpSystem::STORAGE_LEVEL_L {
            self.boiler_state = false;
        } else {
            self.hp_state = 1.;
        }

        if storage_state >= BuildingHeatpumpSystem::STORAGE_LEVEL_HH {
            self.hp_state = 0.;
        }
    }
}
