# energysys_components

## Description
Energy conversion component class with quasi-static state change methods.

Energy conversion component object described by (dataclass EConversionParams):

![image](https://github.com/fkuschel/energysys_components/assets/94350939/f3fd6bcb-c6d1-4e61-bbc8-6f2dfcd93c14)

+ Heatup/Startup Energy [kWh]
 + Cool down time [min]

Energy conversion component object state described by (dataclass EConversionState):
![image](https://github.com/fkuschel/energysys_components/assets/94350939/41fc19ab-0390-4014-99ab-13dce38f4a63)


## Example 
![image](https://github.com/fkuschel/energysys_components/assets/94350939/8c119d76-6278-4d41-9adb-fa35a3c4ca2a)

```math
\begin{align*}
&\textbf{Startup / Heatup definitions} \\
&\text{Startup preparation time} &  &t_{preparation}  & &[minutes] \\
&\text{Startup energy} &  &W_{preparation}  & &[kWh] \\
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
