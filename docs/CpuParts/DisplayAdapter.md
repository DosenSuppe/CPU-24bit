# Display Adapter Chip
The display adapter chip is used to draw onto a the logisim LED-Matrix.

As of now it supports displays with a resolution of up to `16x24` pxiels.

## Inputs
- 1x 24-Bit data input pin
- 1x 27-Bit address input pin
- 1x 1-Bit clear input pin

## Outputs
- 16x 24-Bit output pins

## How to use it
In order to easily draw to the display, it's recommended to use the [display driver](./DisplayDriver.md).

The 27-Bit address pin is connected to an available southbridge pin. The first 24 bits define the address space for the columns of the LED-Matrix. The remaining 3 bits represent the [Mode](./Mode.md).

The 24-Bit data pin is connected directly to the bus.
The data of each column is formatted in a bit-map format.

To clear the display, the clear-pin can be used, or via the display driver's `ClearScreen` and `ClearBuffer` functions.

## Appearance
![Appearance](./img/DisplayAdapter/Appearance.png)

## Internal logic
![Internals](./img/DisplayAdapter/Internals.png)