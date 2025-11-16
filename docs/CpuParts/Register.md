# Register

The Register component can store a 24 bit value. It has many uses across the entire CPU design.

## Inputs
- Data (24 Bit)
- [Mode](./Mode.md) (3 Bit)
- Clock (1 Bit)
- Clear (1 Bit)

## Outputs
- Data-Out (24 Bit)
- Data-Out-Address (24 Bit)
- Display-Data (24 Bit)

## Apperance
![appearance](./img/Register/Appearance.png)

D-In => Data input <br>
Mode => Register Mode input <br>
Clock => Clock signal input <br>
Clr => Clear signal input <br>
D Out => Data output (on demand) <br>
Out => Data output (permenant) <br>
A Out => Data output (on address bus)

## Internal logic
![internals](./img/Register/Internals.png)