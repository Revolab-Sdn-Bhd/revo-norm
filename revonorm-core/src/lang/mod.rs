//! Language pack definitions — one module per language.

pub mod en;
pub mod id;
pub mod ms;
pub mod zh;

use crate::langpack::LanguagePack;

/// All shipped packs, in registration order. Adding a language = adding a
/// module + one entry here.
pub fn all_packs() -> Vec<&'static LanguagePack> {
    vec![ms::pack(), en::pack(), id::pack(), zh::pack(), zh::pack_zh_my()]
}
