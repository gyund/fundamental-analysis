!!! warning "Experimental"
    This is currently very experimental. The current state consists of essentially having training data and data to analyze get processed by the model. However, that's about it.

To get started, you need to install the tensorflow dependencies:

=== "pip"
    ```sh
    pip install stocktracer[tensorflow]
    ```

=== "git"
    ```sh
    poetry install --sync --extras "tensorflow" 
    ```

The idea with this analysis module is to leverage tensorflow to create a training model of stocks that match a particular criteria and ones that don't. For example, label a group of stocks as "good" and another group as "bad". Then use the tensorflow decision trees to categorize other unknown stocks as "good" or "bad" based on their attributes.

## Example

=== "command"
    ```sh
    --8<-- "docs/.smoke-tests/tensorflow.cmd"
    ```

=== "output"
    ```csv
    --8<-- "docs/.smoke-tests/tensorflow.txt"
    ```