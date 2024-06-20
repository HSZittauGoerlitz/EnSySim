#[derive(Clone)]
pub struct CellManager {
    generation_e: f32,
    load_e: f32,
    generation_t: f32,
    load_t: f32,
    contribution_e: f32, // Contribution of cell systems to electrical supply
    contribution_t: f32, // Contribution of cell systems to thermal supply
    fuel_used: f32 // fuel used by cell systems
}

/// An Object which handles the complete cell state. This is comparable to a
/// Gateway, which collects and distributes all information needed for
/// control tasks and comparable.
impl CellManager{
    pub fn new() -> Self
    {
        CellManager {
            generation_e: 0.,
            load_e: 0.,
            generation_t: 0.,
            load_t: 0.,
            contribution_e: 0.,
            contribution_t: 0.,
            fuel_used: 0.
        }
    }

    /// Returns all state values as tuple, so it can easily be send to python
    pub fn get_state(&self) -> (&f32, &f32, &f32, &f32, &f32, &f32, &f32)
    {
        (&self.generation_e, &self.load_e, &self.generation_t, &self.load_t,
         &self.contribution_e, &self.contribution_t, &self.fuel_used
        )
    }

    pub fn update(&mut self, generation_e: &f32, load_e: &f32,
                  generation_t: &f32, load_t: &f32,
                  cont_e: &f32, cont_t: &f32, fuel_used: &f32)
    {
        self.generation_e = *generation_e;
        self.load_e = *load_e;
        self.generation_t = *generation_t;
        self.load_t = *load_t;
        self.contribution_e = *cont_e;
        self.contribution_t = *cont_t;
        self.fuel_used = *fuel_used;
    }
}