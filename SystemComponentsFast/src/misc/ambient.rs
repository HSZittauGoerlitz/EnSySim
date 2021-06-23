pub struct AmbientParameters {
    pub irradiation_dir: f32,
    pub irradiation_diff: f32,
    pub irradiation_glob: f32,
    pub solar_elevation: f32,
    pub solar_azimuth: f32,
    pub specific_gains: [f32; 4],
    pub t_out: f32,
}

impl AmbientParameters {
    pub fn new(direct: f32,
               diffuse: f32,
               elevation: f32,
               azimuth: f32,
               t_out: f32,
            ) -> Self {

        let irradiation_glob = direct + diffuse;
        let specific_gains = [0., 0., 0., 0.];

        AmbientParameters {irradiation_dir: direct,
                           irradiation_diff: diffuse,
                           irradiation_glob: irradiation_glob,
                           solar_elevation: elevation,
                           solar_azimuth: azimuth,
                           specific_gains: specific_gains,
                           t_out: t_out
                           }
    }

    /// Returns eg, sun position and temperature as tuple, so it can easily
    /// be send to python.
    pub fn get_values(&self) -> (&f32, &f32, &f32, &f32)
    {
        (&self.irradiation_glob,
         &self.solar_elevation, &self.solar_azimuth,
         &self.t_out
         )
    }
}
