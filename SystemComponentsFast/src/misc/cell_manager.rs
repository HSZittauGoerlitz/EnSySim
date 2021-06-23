#[derive(Clone)]
pub struct CellManager {
    generation_e: f32,
    load_e: f32,
    generation_t: f32,
    load_t: f32,
}

/// An Object wich handles the complete cell state. This is comparable to a
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
        }
    }

    pub fn update(&mut self, generation_e: &f32, load_e: &f32,
                  generation_t: &f32, load_t: &f32)
    {
        self.generation_e = *generation_e;
        self.load_e = *load_e;
        self.generation_t = *generation_t;
        self.load_t = *load_t;
    }
}