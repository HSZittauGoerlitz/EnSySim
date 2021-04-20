pub struct Environment {
    pub irradiation_dir: f32,
    pub irradiation_diff: f32,
    pub irradiation_glob: f32,
    pub solar_elevation: f32,
    pub solar_azimuth: f32,
    pub specific_gains: [f32; 4],
    pub t_out: f32,
}

impl Environment {
    pub fn new(direct: f32,
               diffuse: f32,
               elevation: f32,
               azimuth: f32,
               t_out: f32,
            ) -> Self {

        let irradiation_glob = direct + diffuse;
        let specific_gains = [0., 0., 0., 0.];

        Environment {irradiation_dir: direct,
                     irradiation_diff: diffuse,
                     irradiation_glob: irradiation_glob,
                     solar_elevation: elevation,
                     solar_azimuth: azimuth,
                     specific_gains: specific_gains,
                     t_out: t_out
                    }
    }
}
