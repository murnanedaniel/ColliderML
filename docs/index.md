# ColliderML

::: warning Dataset Migration in Progress
⚠️ The dataset is currently being migrated to a public location. Some downloads may be temporarily unavailable. Please check back soon or contact us for more information.
:::

<AboutData>

The ColliderML dataset is the largest-yet source of full-detail simulation in a virtual detector experiment.

**Why virtual?** The simulation choices are not tied to a construction timeline, there are no budget limitations, no politics. The only goals are to produce the most realistic physics on a detailed detector geometry, with significant computating challenges, in an ML-friendly structure.

Here is an example collision:

<div class="phoenix-container">
  <iframe 
    src="https://hepsoftwarefoundation.org/phoenix/atlas"
    style="width: 100%; height: 600px; border: none; border-radius: 8px; box-shadow: var(--vp-shadow-2);"
    title="Phoenix Event Display"
    loading="lazy"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  ></iframe>
</div>

<style>
.phoenix-container {
  margin: 2rem 0;
}
</style>

All of the data in this visualisation is available to inspect, including mappings between objects and performance benchmarks of those reconstructed objects.

</AboutData>

## Get the Data

1. Create an environment
```bash
conda create -n colliderml python=3.10
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

3. Run `colliderml download` with your configuration:

<DataConfig />


