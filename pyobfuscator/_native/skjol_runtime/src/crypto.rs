use aes_gcm::aead::{Aead, KeyInit, Payload};
use aes_gcm::{Aes256Gcm, Nonce};
use hkdf::Hkdf;
use sha2::Sha256;
use zeroize::Zeroizing;

const HKDF_CONTEXT: &[u8] = b"skjol-native-v1";

pub fn decrypt(
    root_key: &[u8; 32],
    artifact_id: &[u8; 16],
    nonce: &[u8; 12],
    header: &[u8],
    ciphertext: &[u8],
) -> Result<Zeroizing<Vec<u8>>, String> {
    let key = derive_key(root_key, artifact_id)?;
    let cipher =
        Aes256Gcm::new_from_slice(key.as_ref()).map_err(|_| "invalid native AES-256-GCM key")?;
    let nonce =
        Nonce::try_from(nonce.as_slice()).map_err(|_| "invalid native AES-256-GCM nonce")?;
    let plaintext = cipher
        .decrypt(
            &nonce,
            Payload {
                msg: ciphertext,
                aad: header,
            },
        )
        .map_err(|_| "native artifact authentication failed")?;
    Ok(Zeroizing::new(plaintext))
}

fn derive_key(root_key: &[u8; 32], artifact_id: &[u8; 16]) -> Result<Zeroizing<[u8; 32]>, String> {
    let hkdf = Hkdf::<Sha256>::new(Some(artifact_id), root_key);
    let mut key = Zeroizing::new([0_u8; 32]);
    hkdf.expand(HKDF_CONTEXT, key.as_mut())
        .map_err(|_| "native HKDF expansion failed")?;
    Ok(key)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hkdf_matches_the_python_builder_vector() {
        let root_key = core::array::from_fn(|index| index as u8);
        let artifact_id = core::array::from_fn(|index| index as u8);

        let key = derive_key(&root_key, &artifact_id).expect("HKDF vector must derive");

        assert_eq!(
            key.as_ref(),
            &[
                0xaf, 0x27, 0x8b, 0x14, 0x23, 0x6f, 0x92, 0x4f, 0xa5, 0x8f, 0x04, 0xfc, 0xf8, 0x32,
                0x0a, 0xdd, 0x08, 0x12, 0xaf, 0xf6, 0x3b, 0x76, 0xa0, 0x4e, 0xbd, 0x8c, 0x2d, 0xa8,
                0x1d, 0xe8, 0xa7, 0xe3,
            ]
        );
    }
}
