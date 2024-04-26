# Import des fonctions à exposer
from .constants import (
    Elements,
    Impurete_Elements,
    ONO_Elements,
    Ferrite_Elements,
    THIELMANN_Elements,
    MAYER_Elements,
    Indicateurs,
    Impurete,
    Ferrite,
    ONO,
    THIELMANN,
    MAYER,
    Quality_ref
)

from .correlation import (
    compute_correlation,
    compute_mean_absolute_correlation,
    print_correlation_results
)

from .linear_regression import (
    linear_regression_with_predict_intervals,
    plot_linear_regression_with_predict_intervals,
    compute_confidence_interval,
    export_IC_data
)

from .outliers import (
    remove_outliers,
    export_outliers_and_cleaned_data,
    plot_and_save
)

from .preprocessing import (
    fusion_and_clean_excel_files,
    add_quality,
    keep_GS_and_add_quality,
    split_GS
)
