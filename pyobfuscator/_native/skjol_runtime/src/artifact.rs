use std::convert::TryInto;

pub const MAGIC: &[u8; 8] = b"SKJNR001";
pub const FORMAT_VERSION: u16 = 1;
pub const CIPHER_SUITE: u16 = 1;
pub const HEADER_LENGTH: usize = 60;
const MAX_METADATA_LENGTH: usize = 1024 * 1024;
const MAX_CIPHERTEXT_LENGTH: usize = 64 * 1024 * 1024;

#[derive(Debug)]
pub struct Artifact<'a> {
    pub header: &'a [u8],
    pub python_major: u8,
    pub python_minor: u8,
    pub metadata_length: usize,
    pub nonce: [u8; 12],
    pub artifact_id: [u8; 16],
    pub ciphertext: &'a [u8],
}

impl<'a> Artifact<'a> {
    pub fn parse(data: &'a [u8]) -> Result<Self, String> {
        if data.len() < HEADER_LENGTH {
            return Err("native artifact is shorter than its fixed header".into());
        }
        if &data[0..8] != MAGIC {
            return Err("invalid native artifact magic".into());
        }
        require_u16(data, 8, FORMAT_VERSION, "format version")?;
        require_u16(data, 10, HEADER_LENGTH as u16, "header length")?;
        require_u16(data, 12, CIPHER_SUITE, "cipher suite")?;
        require_u16(data, 14, 0, "flags")?;
        require_u16(data, 18, 0, "reserved field")?;

        let metadata_length = read_u32(data, 20)? as usize;
        let ciphertext_length = usize::try_from(read_u64(data, 24)?)
            .map_err(|_| "ciphertext length does not fit this platform")?;
        if metadata_length > MAX_METADATA_LENGTH {
            return Err("native metadata exceeds the supported limit".into());
        }
        if !(16..=MAX_CIPHERTEXT_LENGTH).contains(&ciphertext_length) {
            return Err("native ciphertext exceeds the supported limit".into());
        }
        let expected_length = HEADER_LENGTH
            .checked_add(ciphertext_length)
            .ok_or("native artifact length overflow")?;
        if data.len() != expected_length {
            return Err(format!(
                "native artifact length mismatch: expected {expected_length}, got {}",
                data.len()
            ));
        }

        Ok(Self {
            header: &data[..HEADER_LENGTH],
            python_major: data[16],
            python_minor: data[17],
            metadata_length,
            nonce: data[32..44]
                .try_into()
                .map_err(|_| "invalid AES-GCM nonce")?,
            artifact_id: data[44..60].try_into().map_err(|_| "invalid artifact ID")?,
            ciphertext: &data[HEADER_LENGTH..],
        })
    }
}

fn require_u16(data: &[u8], offset: usize, expected: u16, field: &str) -> Result<(), String> {
    let actual = read_u16(data, offset)?;
    if actual != expected {
        return Err(format!("unsupported native {field}: {actual}"));
    }
    Ok(())
}

fn read_u16(data: &[u8], offset: usize) -> Result<u16, String> {
    let bytes = data
        .get(offset..offset + 2)
        .ok_or("truncated native u16 field")?
        .try_into()
        .map_err(|_| "invalid native u16 field")?;
    Ok(u16::from_le_bytes(bytes))
}

fn read_u32(data: &[u8], offset: usize) -> Result<u32, String> {
    let bytes = data
        .get(offset..offset + 4)
        .ok_or("truncated native u32 field")?
        .try_into()
        .map_err(|_| "invalid native u32 field")?;
    Ok(u32::from_le_bytes(bytes))
}

fn read_u64(data: &[u8], offset: usize) -> Result<u64, String> {
    let bytes = data
        .get(offset..offset + 8)
        .ok_or("truncated native u64 field")?
        .try_into()
        .map_err(|_| "invalid native u64 field")?;
    Ok(u64::from_le_bytes(bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_truncated_header() {
        assert!(Artifact::parse(b"SKJNR001").is_err());
    }
}
