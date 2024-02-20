# energysys_components

## Description
Energy conversion component class with quasi-static state change methods.

A Python-based simulation tool was developed to analyse energy conversion systems in an early concept phase, where energy conversion components are described by technical and economic specifications in form of surrogate models. These models provide uniform, simplified descriptions of dynamic behaviour such as start-up, heat-up and load change in temporal and energetic terms. Exemplary components include fuel cells, batteries and gas reformers. Multiple different components are linked via enthalpy flow to form a single dependent energy conversion path. A system can comprised of several different paths.


Parameter of EnergyConversion-objects, initialized with EConversionParams (DataClass):

```math
\begin{align*}
&\textbf{Startup / Heatup definitions} \\
&\text{Startup preparation time} &  &t_{preparation}  & &[minutes] \\
&\text{Startup energy} &  &E_{preparation}  & &[kWh] \\
&\text{Startup efficiency} &  &\eta_{preparation}  & &[kWh] \\

&\textbf{Load operation definitions} \\
&\text{Minimum Output Power} &  &P_{out,min}  & &[\%] \\
&\text{Rated Output Power} &  &P_{out,rated}  & &[kW] \\
&\text{Load Change pos.} &  &p_{change,pos}  & &[\%/min] \\
&\text{Load Change neg.} &  &p_{change,neg}  & &[\%/min] \\
&\text{Load Change Energy} &  &E_{change}=f(P_{out})  & &[kWh] \\

&\textbf{Efficiency definitions} \\
&\text{Overall efficiency curve} &  &\eta=f(P_{out})  & &[\%] \\
&\text{Main conversion efficiency curve} &  &\eta_{mc}=f(P_{out})  & &[\%] \\

&\textbf{Shutdown definitions} \\
&\text{Cooldown time} &  &t_{cooldown}  & &[minutes] \\
&\textbf{Input Energy Split definitions} \\
&\text{Secondary Input Split} &  &split_{P\_sd}  & &[-,-] \\

&\textbf{Techno-economic definitions} \\
&\text{Investment Costs} &  &p_{Eur}  & &[Eur/kW] \\
&\text{Volume} &  &p_{vol}  & &[m^3/kW] \\
&\text{Weight} &  &t_{mass}  & &[kg/kW] \\
\end{align*}
```

State of EnergyConversion-objects, described with EConversionState-object (DataClass):

```math
\begin{align*}
&\textbf{Combined Input} \\
&\text{Combined input energy} &  &E_{in}  & &[kWh] \\
&\text{Combined input power} &  &P_{in}  & &[kW] \\
&\textbf{Main Conversion Path Input} \\
&\text{Main conversion input energy} &  &E_{in,mc}  & &[kWh] \\
&\text{Main conversion input power} &  &P_{in,mc}  & &[kW] \\
&\textbf{Secondary 1 Input} \\
&\text{Secondary 1 input energy} &  &E_{in,sd1}  & &[kWh] \\
&\text{Secondary 1 input power} &  &P_{in,sd1}  & &[kW] \\
&\textbf{Secondary 2 Input} \\
&\text{Secondary 2 input energy} &  &E_{in,sd2}  & &[kWh] \\
&\text{Secondary 2 input power} &  &P_{in,sd2}  & &[kW] \\
&\textbf{Combined Output} \\
&\text{Combined output energy} &  &E_{out}  & &[kWh] \\
&\text{Combined output power} &  &P_{out}  & &[kW] \\
&\textbf{Loss} \\
&\text{Loss energy} &  &E_{loss}  & &[kWh] \\
&\text{Loss power} &  &P_{loss}  & &[kW] \\
&\textbf{Heatup} \\
&\text{Heatup state} &  &HU  & &[\%] \\
&\textbf{Efficiencies} \\
&\text{Overall efficiency} &  &\eta  & &[\%] \\
&\text{Main conversion efficiency} &  &\eta_{mc}  & &[\%] \\
&\textbf{Techno-economic} \\
&\text{Opex} &  &opex  & &[Eur] \\
\end{align*}
```

![image](https://github.com/ZBT-Tools/energysys_components/assets/94350939/42a7fe7a-4aef-4df6-8b4d-f8af7aa51c4f)



## Example 

![image](https://github.com/ZBT-Tools/energysys_components/assets/94350939/4dac6e90-344b-4f3d-aa67-7cf2a9963733)

![image](https://github.com/ZBT-Tools/energysys_components/assets/94350939/403d5eee-5da4-4c14-bd27-46b8c0b7b5de)
