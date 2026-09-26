"""Authored, executable positive control, not third-party code or real-world incidence.

The scaler intentionally sees all rows before splitting. The final fit does not
undo that fact. For the source-prefix check, stop at the DOWNSTREAM marker.
"""

from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

data = load_wine()
scaler = StandardScaler()
scaled = scaler.fit_transform(data.data)
x_train, x_test, y_train, y_test = train_test_split(
    scaled, data.target, test_size=0.3, random_state=0, stratify=data.target
)
# DOWNSTREAM
model = DecisionTreeClassifier(max_depth=3, random_state=0)
model.fit(x_train, y_train)

assert int(scaler.n_samples_seen_) == len(data.target)
assert int(scaler.n_samples_seen_) > len(x_train)
