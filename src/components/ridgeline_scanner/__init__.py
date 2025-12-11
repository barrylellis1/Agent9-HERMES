import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "ridgeline_scanner",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component("ridgeline_scanner", path=build_dir)


def ridgeline_scanner(
    data, 
    categories, 
    key=None, 
    height=400, 
    colors=None,
    title="Margin Distribution Scanner"
):
    """
    Displays an animated Ridgeline Plot (Joyplot) to visualize distribution shapes across dimensions.
    
    Parameters
    ----------
    data : list of lists or list of dicts
        The distribution data for each ridgeline. 
        Example: [[0.1, 0.2, ...], [0.3, 0.4, ...]]
    
    categories : list of str
        Labels for each ridgeline (y-axis labels).
        Example: ["North America", "Europe", "APAC"]
        
    height : int
        Height of the component in pixels.
        
    colors : list of str, optional
        Hex color codes for the gradients.
        
    title : str
        Chart title.
        
    key : str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.
    """
    return _component_func(
        data=data,
        categories=categories,
        height=height,
        colors=colors,
        title=title,
        key=key,
        default=None
    )


# --- Test Harness ---
if not _RELEASE:
    import streamlit as st
    import numpy as np

    st.subheader("Ridgeline Scanner Debug")

    # Generate dummy data
    # 3 Dimensions (Regions), 50 data points each
    categories = ["North America", "Europe", "Asia Pacific"]
    
    # Generate distributions with different shapes
    # NA: Normal distribution (Stable)
    dist_na = np.random.normal(0, 1, 100).tolist()
    
    # EU: Bi-modal (Split market)
    dist_eu = np.concatenate([
        np.random.normal(-2, 0.5, 50),
        np.random.normal(2, 0.5, 50)
    ]).tolist()
    
    # APAC: Skewed negative (Problem area)
    dist_apac = np.random.exponential(1.5, 100) * -1
    dist_apac = dist_apac.tolist()

    data = [dist_na, dist_eu, dist_apac]

    st.write("Visualizing distribution shapes across 3 regions:")
    
    ridgeline_scanner(
        data=data,
        categories=categories,
        height=500,
        title="Margin Variance by Region"
    )
