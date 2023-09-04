# energysys_components

## Description
Energy conversion component class with quasi-static state change methods.

EnergyConversion-Objects are initialized with EConversionParams-Objects (DataClass):

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
&\textbf{Efficiency definitions} \\
&\text{Overall efficiency curve} &  &\eta=f(P)  & &[\%] \\
&\text{Main conversion efficiency curve} &  &\eta_{mc}=f(P)  & &[\%] \\
&\textbf{Shutdown definitions} \\
&\text{Cooldown time} &  &t_{cooldown}  & &[minutes] \\
&\textbf{Input Energy Split definitions} \\
&\text{Secondary Input Split} &  &split_{P\_sd}  & &[-,-] \\
&\textbf{Techno-economic definitions} \\
&\text{Investment Costs} &  &p_{\euro{}}  & &[\euro{}/kW] \\
&\text{Volume} &  &p_{vol}  & &[m^3/kW] \\
&\text{Weight} &  &t_{mass}  & &[kg/kW] \\
\end{align*}
```

Energy conversion component object state described EConversionState-Object (DataClass):

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
&\text{Opex} &  &opex  & &[\euro{}] \\
\end{align*}
```


## Example 
![image](https://github.com/fkuschel/energysys_components/assets/94350939/8c119d76-6278-4d41-9adb-fa35a3c4ca2a)

