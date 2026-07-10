// i18n key registration for table columns and actions.
// Keys are referenced dynamically in GenericDataTable via COLUMN_I18N
// and ACTION_I18N mappings; static calls here ensure the extractor
// picks them up.
import { t } from "./i18n";

t("tables.column.moduleName", "Module");
t("tables.column.totalLines", "Lines");
t("tables.column.relativePath", "File");
t("tables.column.source", "Source");
t("tables.column.target", "Target");
t("tables.column.relationType", "Relation type");
t("tables.action.openFiles", "Open files");
t("tables.action.drilldown", "Open files");
