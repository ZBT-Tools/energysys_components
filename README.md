
# energysys_components

## Description
Energy conversion component class with transient state change methods.

A Python-based simulation tool to analyse energy conversion systems in an early concept phase, where energy conversion components are described by technical and economic specifications in form of surrogate models. These models provide uniform, simplified descriptions of dynamic behaviour such as start-up, heat-up and load change in temporal and energetic terms. Exemplary components include fuel cells, batteries and gas reformers. 

Multiple different components can be linked via enthalpy flow to form a single dependent energy conversion path. A system can be comprised of several different paths.

System topology generation and control algorithms are published in:

https://github.com/ZBT-Tools/energysys_control

### Unified 0D Component Model
#### General Description
<img src="docs/img/readme_component.png" width="400">

#### Examples

<img alt="img.png" src="docs/img/readme_component_examples.png" width="400"/>

#### Input and output definition

<img alt="img.png" src="docs/img/readme_component_input.png" width="440"/>

#### Parameter definition

<img alt="img.png" src="docs/img/readme_component_parameter.png" width="450"/>

#### State definition

<img alt="img.png" src="docs/img/readme_component_state.png" width="300"/>

#### Example 

<img alt="img.png" src="docs/img/readme_component_t1.png"/>
<img alt="img_1.png" src="docs/img/readme_component_t2.png"/>

---


<img src="docs/img/bmbf.png" width="200">