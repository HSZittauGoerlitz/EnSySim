// external
use pyo3::prelude::*;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Wind {
    height: f32,  // height of hub
    area: f32,  // effective rotor area
    efficiency: f32, // simple effiency factor, TODO: curve
    min_ws: f32, // minimum wind speed where electricity production starts
    opt_ws: f32, // optimal working point at hub height
    max_ws: f32, // maximum wind speed
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Wind {
    ///  Create wind plant with specific hub height and blade radius
    ///
    /// # Arguments
    /// * ?
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(height: f32, radius: f32, min_ws: f32, opt_ws: f32, max_ws: f32, 
               efficiency: f32, hist: usize) -> Self {
        
        let pi = std::f32::consts::PI;
        let area = pi / 2. * radius.powf(2.);

        let gen_e;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
        }

        let wind = Wind {height: height,
                        area: area,
                        efficiency: efficiency,
                        min_ws: min_ws,
                        opt_ws: opt_ws,
                        max_ws: max_ws,
                        gen_e: gen_e,
                        };
        wind
    }
}

/// wind plant
impl Wind {
    fn save_hist(&mut self, power_e: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*power_e)
            },
        }
    }

    /// Calculate current electrical power
    ///
    /// # Arguments
    /// * 
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self, ws: &f32) -> f32 {
        // ToDo: could be temperature dependent
        let air_density = 1.2; // kg/m³
        // ToDo: could be parameter
        let z0 = 0.1; // [m] roughness length for agricultural land with a few buildings and 8 m high hedges seperated by approx. 500 m
        // https://wind-data.ch/tools/profile.php?h=10&v=5&z0=0.1&abfrage=Refresh
        let mut ws_hub = ws * (self.height / z0).ln() / (10. / z0).ln();

        // calculate electrical power generated
        // https://rechneronline.de/wind-power/
        let power_e: f32;

        if ws_hub < self.min_ws || ws_hub > self.max_ws {
            power_e = 0.;
        }
        else {
            if ws_hub > self.opt_ws {
                ws_hub = self.opt_ws;
            }
            power_e = self.area * air_density * ws_hub.powf(3.) * self.efficiency;
        }

        // save data
        self.save_hist(&power_e);

        return power_e;
    }
}