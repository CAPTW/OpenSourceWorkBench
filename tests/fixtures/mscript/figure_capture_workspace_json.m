x = [0, 1, 2];
temperature = [300, 315, 330];
fid = fopen('workspace_summary.json', 'w');
fprintf(fid, '{"variables":[{"name":"x","type_name":"double","shape":[1,3],"dtype":"float64","size":3,"preview":"[0,1,2]"}]}');
fclose(fid);
