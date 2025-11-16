# Programmable Interrupt Controller (PIC)

The PIC is a dedicated hardware chip responsible for managing multiple interrupt requests from various devices before passing them on to the CPU.

Its function is to prevent chaos by acting as a traffic cop between fast-acting hardware devices and the CPU's core processing tasks.

In this project, the PIC has 7 interrupt request lines (IRQ-Lines) which can be connected to devices.

----

## Inputs
- Read-Interrupt-ID (1 Bit)
- Read-Interrupt-Data (1 Bit)
- Interrupt-Acknowledge (1 Bit)
- Device0-In -> Device6-In (7x 25 Bit each)

## Outputs
- Interrupt-Out (1 Bit)
- Interrupt-Data-Out (24 Bit)
- Interrupt-ID-Out (24 Bit)

## Input format
The 25 Bit input is split into two segments.
- Bits 0 -> 24 are Data
- Bit 25 is the IRQ-Signal, set this bit to HIGH when you want to trigger an interrupt

## How to connect a device
1. Connect a device to one of the 7 device inputs
2. Make sure that your software handles the interrupt through the [ResetVector]() correctly
3. Trigger the interrupt, data is optional to provide

## Appearance
![Appearance](./img/PIC/Appearance.png)

## Internal logic
![Internals](./img/PIC/Internals.png)


