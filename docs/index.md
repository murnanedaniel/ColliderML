# ColliderML

::: warning Dataset Migration in Progress
⚠️ The dataset is currently being migrated to a public location. Some downloads may be temporarily unavailable. Please check back soon or contact us for more information.
:::

<AboutData>

The ColliderML dataset is the largest-yet source of full-detail simulation in a virtual detector experiment.

**Why virtual?** The simulation choices are not tied to a construction timeline, there are no budget limitations, no politics. The only goals are to produce the most realistic physics on a detailed detector geometry, with significant computating challenges, in an ML-friendly structure.

The ColliderML dataset provides comprehensive simulation data for machine learning applications in high-energy physics, with detailed detector responses and physics object reconstructions.

</AboutData>

## Get the Data

1. Create an environment
```bash
conda create -n colliderml-env python=3.11
conda activate colliderml-env
```
2. Pip install
```bash
pip install colliderml
```

<!-- ::: tip New to ColliderML? -->
<details class="custom-block">
<summary>👉 New to ColliderML? Click here for optional introductory data download</summary>

3. Run `colliderml taster --notebooks` to get a small test dataset and example notebooks
4. Open the intro notebook (or follow along in the [Tutorials](/tutorials) section)

</details>
<!-- ::: -->

3. Run `colliderml get` with your configuration:

<DataConfig />


